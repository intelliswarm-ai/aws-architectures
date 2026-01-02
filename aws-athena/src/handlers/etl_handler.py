"""Lambda handler for ETL job orchestration.

This handler triggers and monitors Glue ETL jobs that transform
JSON data to Apache Parquet format with Snappy compression.
"""

import json
import logging
from datetime import datetime
from typing import Any

from ..common.config import settings
from ..common.exceptions import ETLJobError
from ..common.models import JobStatus, PartitionSpec
from ..services import get_glue_service, get_s3_service

logger = logging.getLogger()
logger.setLevel(settings.log_level)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle ETL job requests.

    Supports:
    - Scheduled triggers (EventBridge)
    - S3 event triggers (new data arrives)
    - Direct invocation with partition specification
    - API Gateway requests

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        ETL job execution result
    """
    logger.info(f"ETL handler invoked: {json.dumps(event, default=str)[:500]}")

    try:
        event_type = _get_event_type(event)

        if event_type == "schedule":
            return _handle_scheduled_etl(event)
        elif event_type == "s3":
            return _handle_s3_trigger(event)
        elif event_type == "api_gateway":
            return _handle_api_request(event)
        else:
            return _handle_direct_invocation(event)

    except ETLJobError as e:
        logger.error(f"ETL job failed: {e}")
        return _error_response(500, str(e), e.job_run_id)
    except Exception as e:
        logger.exception(f"ETL handler error: {e}")
        return _error_response(500, str(e))


def _get_event_type(event: dict[str, Any]) -> str:
    """Determine event source type."""
    if "httpMethod" in event or "requestContext" in event:
        return "api_gateway"
    elif "detail-type" in event:
        return "schedule"
    elif "Records" in event and event["Records"]:
        if "s3" in event["Records"][0]:
            return "s3"
    return "direct"


def _handle_scheduled_etl(event: dict[str, Any]) -> dict[str, Any]:
    """Handle scheduled ETL execution (e.g., hourly via EventBridge)."""
    glue_service = get_glue_service()

    # Get the previous hour's partition for processing
    from datetime import timedelta

    now = datetime.utcnow()
    previous_hour = now - timedelta(hours=1)
    partition = PartitionSpec.from_datetime(previous_hour)

    # Start ETL job with partition arguments
    job_arguments = {
        "--partition_year": partition.year,
        "--partition_month": partition.month,
        "--partition_day": partition.day,
        "--partition_hour": partition.hour or "00",
        "--source_path": f"s3://{settings.raw_bucket}/raw/{partition.path}/",
        "--target_path": f"s3://{settings.processed_bucket}/processed/{partition.path}/",
    }

    job_run_id = glue_service.start_etl_job(arguments=job_arguments)

    logger.info(f"Started scheduled ETL job: {job_run_id} for partition {partition.path}")

    return {
        "status": "started",
        "job_name": settings.glue_etl_job_name,
        "job_run_id": job_run_id,
        "partition": partition.path,
        "trigger": "schedule",
    }


def _handle_s3_trigger(event: dict[str, Any]) -> dict[str, Any]:
    """Handle S3 event trigger when new data arrives."""
    glue_service = get_glue_service()

    # Extract S3 information from event
    records = event.get("Records", [])
    source_paths = []

    for record in records:
        s3_info = record.get("s3", {})
        bucket = s3_info.get("bucket", {}).get("name")
        key = s3_info.get("object", {}).get("key", "")

        if bucket and key:
            # Extract partition from key
            source_paths.append(f"s3://{bucket}/{key}")

    if not source_paths:
        return {"status": "skipped", "reason": "No valid S3 paths in event"}

    # Start ETL job with source paths
    job_arguments = {
        "--source_paths": ",".join(source_paths),
        "--target_bucket": settings.processed_bucket,
        "--incremental": "true",
    }

    job_run_id = glue_service.start_etl_job(arguments=job_arguments)

    logger.info(f"Started S3-triggered ETL job: {job_run_id}")

    return {
        "status": "started",
        "job_name": settings.glue_etl_job_name,
        "job_run_id": job_run_id,
        "source_paths": source_paths,
        "trigger": "s3",
    }


def _handle_api_request(event: dict[str, Any]) -> dict[str, Any]:
    """Handle API Gateway request for ETL operations."""
    glue_service = get_glue_service()

    body = event.get("body", "{}")
    if event.get("isBase64Encoded"):
        import base64

        body = base64.b64decode(body).decode("utf-8")

    data = json.loads(body)
    action = data.get("action", "start")

    if action == "start":
        # Start new ETL job
        partition_data = data.get("partition")
        if partition_data:
            partition = PartitionSpec(**partition_data)
        else:
            partition = PartitionSpec.from_datetime(datetime.utcnow())

        job_arguments = {
            "--partition_year": partition.year,
            "--partition_month": partition.month,
            "--partition_day": partition.day,
            "--partition_hour": partition.hour or "00",
            "--source_path": f"s3://{settings.raw_bucket}/raw/{partition.path}/",
            "--target_path": f"s3://{settings.processed_bucket}/processed/{partition.path}/",
        }

        wait_for_completion = data.get("wait", False)

        job_run_id = glue_service.start_etl_job(arguments=job_arguments)

        if wait_for_completion:
            job_run = glue_service.wait_for_job_completion(job_run_id)
            return _api_response(
                200,
                {
                    "status": job_run.status.value,
                    "job_run_id": job_run_id,
                    "execution_time_seconds": job_run.execution_time_seconds,
                },
            )

        return _api_response(
            202,
            {
                "status": "started",
                "job_run_id": job_run_id,
                "partition": partition.path,
            },
        )

    elif action == "status":
        job_run_id = data.get("job_run_id")
        if not job_run_id:
            return _api_response(400, {"error": "job_run_id required"})

        job_run = glue_service.get_job_run(job_run_id)
        return _api_response(
            200,
            {
                "job_run_id": job_run_id,
                "status": job_run.status.value,
                "started_on": job_run.started_on.isoformat(),
                "completed_on": job_run.completed_on.isoformat() if job_run.completed_on else None,
                "execution_time_seconds": job_run.execution_time_seconds,
                "error_message": job_run.error_message,
            },
        )

    elif action == "stop":
        job_run_id = data.get("job_run_id")
        if not job_run_id:
            return _api_response(400, {"error": "job_run_id required"})

        glue_service.stop_job_run(job_run_id)
        return _api_response(200, {"status": "stopping", "job_run_id": job_run_id})

    elif action == "crawler":
        # Start Glue crawler to update catalog
        glue_service.start_crawler()
        return _api_response(
            202,
            {
                "status": "started",
                "crawler_name": settings.glue_crawler_name,
            },
        )

    else:
        return _api_response(400, {"error": f"Unknown action: {action}"})


def _handle_direct_invocation(event: dict[str, Any]) -> dict[str, Any]:
    """Handle direct Lambda invocation for ETL jobs."""
    glue_service = get_glue_service()

    action = event.get("action", "start")

    if action == "start":
        # Extract partition from event or use current time
        if "partition" in event:
            partition = PartitionSpec(**event["partition"])
        else:
            partition = PartitionSpec.from_datetime(datetime.utcnow())

        job_arguments = event.get("arguments", {})
        job_arguments.update(
            {
                "--partition_year": partition.year,
                "--partition_month": partition.month,
                "--partition_day": partition.day,
                "--partition_hour": partition.hour or "00",
            }
        )

        job_run_id = glue_service.start_etl_job(
            job_name=event.get("job_name"),
            arguments=job_arguments,
        )

        # Optionally wait for completion
        if event.get("wait", False):
            timeout = event.get("timeout", 3600)
            job_run = glue_service.wait_for_job_completion(
                job_run_id,
                job_name=event.get("job_name"),
                timeout=timeout,
            )
            return {
                "status": job_run.status.value,
                "job_run_id": job_run_id,
                "execution_time_seconds": job_run.execution_time_seconds,
                "dpu_seconds": job_run.dpu_seconds,
            }

        return {
            "status": "started",
            "job_run_id": job_run_id,
            "partition": partition.path,
        }

    elif action == "status":
        job_run_id = event.get("job_run_id")
        job_run = glue_service.get_job_run(job_run_id, event.get("job_name"))
        return {
            "job_run_id": job_run_id,
            "status": job_run.status.value,
            "started_on": job_run.started_on.isoformat(),
            "completed_on": job_run.completed_on.isoformat() if job_run.completed_on else None,
        }

    elif action == "crawler":
        crawler_name = event.get("crawler_name")
        wait = event.get("wait", False)

        glue_service.start_crawler(crawler_name)

        if wait:
            crawler_run = glue_service.wait_for_crawler_completion(crawler_name)
            return {
                "status": crawler_run.status.value,
                "tables_created": crawler_run.tables_created,
                "tables_updated": crawler_run.tables_updated,
            }

        return {"status": "started", "crawler_name": crawler_name or settings.glue_crawler_name}

    return {"status": "error", "message": f"Unknown action: {action}"}


def _api_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Create API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }


def _error_response(
    status_code: int, message: str, job_run_id: str | None = None
) -> dict[str, Any]:
    """Create error response."""
    body = {"error": message}
    if job_run_id:
        body["job_run_id"] = job_run_id
    return _api_response(status_code, body)
