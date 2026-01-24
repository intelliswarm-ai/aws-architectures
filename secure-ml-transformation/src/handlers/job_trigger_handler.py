"""Lambda handler for triggering Glue ETL jobs."""

import json
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.models import AuditEventType, AuditLogEntry
from src.services.audit_service import AuditService
from src.services.glue_service import GlueService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Trigger Glue ETL job for data transformation.

    This handler can be triggered by:
    - S3 event notifications (new data arrival)
    - EventBridge scheduled events
    - Manual invocation via API Gateway

    Args:
        event: Lambda event payload
        context: Lambda context

    Returns:
        Job trigger response with job run ID
    """
    settings = get_settings()
    glue_service = GlueService()
    audit_service = AuditService()

    # Determine trigger source and extract parameters
    trigger_source = _determine_trigger_source(event)
    job_parameters = _extract_job_parameters(event, trigger_source)

    logger.info(
        "Triggering Glue job",
        extra={
            "trigger_source": trigger_source,
            "job_parameters": job_parameters,
        },
    )

    # Log job start audit event
    audit_entry = AuditLogEntry(
        timestamp=datetime.utcnow(),
        event_type=AuditEventType.JOB_START,
        job_execution_id="pending",
        job_name=f"{settings.resource_prefix}-main-etl",
        action="StartJobRun",
        details={
            "trigger_source": trigger_source,
            "parameters": job_parameters,
        },
        status="IN_PROGRESS",
    )
    audit_service.log_event(audit_entry)

    try:
        # Start the Glue job
        job_run_id = glue_service.start_job(
            job_name=f"{settings.resource_prefix}-main-etl",
            arguments=job_parameters,
        )

        # Update audit with job run ID
        audit_entry.job_execution_id = job_run_id
        audit_entry.status = "SUCCESS"
        audit_entry.details["job_run_id"] = job_run_id
        audit_service.log_event(audit_entry)

        logger.info("Glue job started successfully", extra={"job_run_id": job_run_id})

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Job triggered successfully",
                    "job_run_id": job_run_id,
                    "job_name": f"{settings.resource_prefix}-main-etl",
                    "trigger_source": trigger_source,
                }
            ),
        }

    except Exception as e:
        logger.exception("Failed to start Glue job")

        # Log failure audit event
        audit_entry.status = "FAILURE"
        audit_entry.event_type = AuditEventType.JOB_FAILED
        audit_entry.details["error"] = str(e)
        audit_service.log_event(audit_entry)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "message": "Failed to trigger job",
                    "error": str(e),
                }
            ),
        }


def _determine_trigger_source(event: dict[str, Any]) -> str:
    """Determine the source that triggered this handler.

    Args:
        event: Lambda event payload

    Returns:
        Trigger source identifier
    """
    if "Records" in event and event["Records"]:
        first_record = event["Records"][0]
        if "s3" in first_record:
            return "s3_event"
        if "eventSource" in first_record and "sqs" in first_record["eventSource"]:
            return "sqs_event"

    if "source" in event and event.get("source") == "aws.events":
        return "eventbridge_schedule"

    if "httpMethod" in event or "requestContext" in event:
        return "api_gateway"

    return "manual"


def _extract_job_parameters(
    event: dict[str, Any],
    trigger_source: str,
) -> dict[str, str]:
    """Extract job parameters based on trigger source.

    Args:
        event: Lambda event payload
        trigger_source: Identified trigger source

    Returns:
        Job parameters for Glue job
    """
    settings = get_settings()
    base_params = {
        "--source_bucket": settings.raw_data_bucket,
        "--target_bucket": settings.processed_data_bucket,
        "--environment": settings.environment,
        "--enable_job_bookmark": "true",
    }

    if trigger_source == "s3_event":
        # Extract S3 path from event
        record = event["Records"][0]["s3"]
        bucket = record["bucket"]["name"]
        key = record["object"]["key"]
        base_params["--source_bucket"] = bucket
        base_params["--source_path"] = f"s3://{bucket}/{key}"

    elif trigger_source == "eventbridge_schedule":
        # Use date-based partitioning
        today = datetime.utcnow().strftime("%Y/%m/%d")
        base_params["--source_path"] = f"s3://{settings.raw_data_bucket}/transactions/{today}/"

    elif trigger_source == "api_gateway":
        # Extract custom parameters from request body
        body = event.get("body", "{}")
        if isinstance(body, str):
            body = json.loads(body)
        base_params.update(
            {f"--{k}": str(v) for k, v in body.items() if k not in ["source_bucket", "target_bucket"]}
        )

    return base_params
