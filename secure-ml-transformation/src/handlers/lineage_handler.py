"""Lambda handler for data lineage tracking and management."""

import json
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.models import JobExecutionStatus, LineageRecord
from src.services.glue_service import GlueService
from src.services.lineage_service import LineageService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Handle lineage tracking operations.

    Supports operations:
    - record_lineage: Record a new lineage entry
    - get_lineage: Retrieve lineage for a job run
    - get_lineage_history: Get lineage history for a dataset
    - update_job_status: Update job execution status

    Args:
        event: Lambda event payload
        context: Lambda context

    Returns:
        Operation response
    """
    settings = get_settings()
    lineage_service = LineageService()
    glue_service = GlueService()

    operation = event.get("operation", "get_lineage")
    logger.info("Processing lineage operation", extra={"operation": operation})

    try:
        if operation == "record_lineage":
            return _record_lineage(event, lineage_service)

        elif operation == "get_lineage":
            return _get_lineage(event, lineage_service)

        elif operation == "get_lineage_history":
            return _get_lineage_history(event, lineage_service)

        elif operation == "update_job_status":
            return _update_job_status(event, lineage_service, glue_service)

        elif operation == "get_job_bookmark":
            return _get_job_bookmark(event, glue_service)

        else:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": f"Unknown operation: {operation}"}),
            }

    except Exception as e:
        logger.exception("Lineage operation failed")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


def _record_lineage(
    event: dict[str, Any],
    lineage_service: LineageService,
) -> dict[str, Any]:
    """Record a new lineage entry.

    Args:
        event: Event with lineage data
        lineage_service: Lineage service instance

    Returns:
        Response with lineage ID
    """
    lineage_data = event.get("lineage", {})

    lineage_record = LineageRecord(
        job_execution_id=lineage_data.get("job_execution_id"),
        job_name=lineage_data.get("job_name"),
        start_time=datetime.fromisoformat(lineage_data.get("start_time")),
        end_time=datetime.fromisoformat(lineage_data["end_time"]) if lineage_data.get("end_time") else None,
        status=JobExecutionStatus(lineage_data.get("status", "RUNNING")),
        input_records=lineage_data.get("input_records", 0),
        output_records=lineage_data.get("output_records", 0),
        filtered_records=lineage_data.get("filtered_records", 0),
        transformations_applied=lineage_data.get("transformations_applied", []),
        input_paths=lineage_data.get("input_paths", []),
        output_paths=lineage_data.get("output_paths", []),
        parameters=lineage_data.get("parameters", {}),
    )

    lineage_id = lineage_service.record_lineage(lineage_record)

    logger.info("Lineage recorded", extra={"lineage_id": lineage_id})

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Lineage recorded successfully",
                "lineage_id": lineage_id,
                "job_execution_id": lineage_record.job_execution_id,
            }
        ),
    }


def _get_lineage(
    event: dict[str, Any],
    lineage_service: LineageService,
) -> dict[str, Any]:
    """Get lineage for a specific job run.

    Args:
        event: Event with job_execution_id
        lineage_service: Lineage service instance

    Returns:
        Response with lineage data
    """
    job_execution_id = event.get("job_execution_id")

    if not job_execution_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "job_execution_id is required"}),
        }

    lineage = lineage_service.get_lineage(job_execution_id)

    if not lineage:
        return {
            "statusCode": 404,
            "body": json.dumps({"error": f"Lineage not found for {job_execution_id}"}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps(lineage.model_dump(mode="json")),
    }


def _get_lineage_history(
    event: dict[str, Any],
    lineage_service: LineageService,
) -> dict[str, Any]:
    """Get lineage history for a dataset or path.

    Args:
        event: Event with dataset path and optional filters
        lineage_service: Lineage service instance

    Returns:
        Response with lineage history
    """
    path = event.get("path")
    limit = event.get("limit", 100)
    start_date = event.get("start_date")
    end_date = event.get("end_date")

    if not path:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "path is required"}),
        }

    history = lineage_service.get_lineage_history(
        path=path,
        limit=limit,
        start_date=datetime.fromisoformat(start_date) if start_date else None,
        end_date=datetime.fromisoformat(end_date) if end_date else None,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "path": path,
                "count": len(history),
                "lineage_records": [h.model_dump(mode="json") for h in history],
            }
        ),
    }


def _update_job_status(
    event: dict[str, Any],
    lineage_service: LineageService,
    glue_service: GlueService,
) -> dict[str, Any]:
    """Update job execution status in lineage.

    Args:
        event: Event with job status update
        lineage_service: Lineage service instance
        glue_service: Glue service instance

    Returns:
        Response with update result
    """
    job_execution_id = event.get("job_execution_id")
    job_name = event.get("job_name")
    new_status = event.get("status")

    if not all([job_execution_id, new_status]):
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "job_execution_id and status are required"}),
        }

    # Get additional details from Glue if job_name provided
    job_details = {}
    if job_name:
        try:
            run_info = glue_service.get_job_run(job_name, job_execution_id)
            job_details = {
                "execution_time": run_info.get("ExecutionTime"),
                "dpu_seconds": run_info.get("DPUSeconds"),
                "error_message": run_info.get("ErrorMessage"),
            }
        except Exception as e:
            logger.warning(f"Could not fetch job run details: {e}")

    lineage_service.update_status(
        job_execution_id=job_execution_id,
        status=JobExecutionStatus(new_status),
        end_time=datetime.utcnow() if new_status in ["SUCCEEDED", "FAILED", "STOPPED"] else None,
        details=job_details,
    )

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "message": "Status updated successfully",
                "job_execution_id": job_execution_id,
                "new_status": new_status,
            }
        ),
    }


def _get_job_bookmark(
    event: dict[str, Any],
    glue_service: GlueService,
) -> dict[str, Any]:
    """Get job bookmark state for lineage tracking.

    Args:
        event: Event with job name
        glue_service: Glue service instance

    Returns:
        Response with bookmark state
    """
    job_name = event.get("job_name")

    if not job_name:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "job_name is required"}),
        }

    bookmark = glue_service.get_job_bookmark(job_name)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "job_name": job_name,
                "bookmark": bookmark,
            }
        ),
    }
