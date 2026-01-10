"""Knowledge base synchronization handler for scheduled and on-demand sync."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.exceptions import KnowledgeBaseError
from src.common.models import ApiResponse
from src.services.knowledge_base_service import KnowledgeBaseService

logger = Logger()
tracer = Tracer()
metrics = Metrics()

settings = get_settings()
knowledge_base_service = KnowledgeBaseService()


@tracer.capture_method
def process_scheduled_sync(event: dict[str, Any]) -> dict[str, Any]:
    """Process scheduled EventBridge sync event."""
    logger.info("Processing scheduled sync event")

    # Get knowledge base ID from event or settings
    knowledge_base_id = event.get("knowledgeBaseId", settings.knowledge_base_id)
    data_source_id = event.get("dataSourceId", settings.knowledge_base_data_source_id)

    if not knowledge_base_id:
        logger.error("No knowledge base ID configured")
        return {
            "success": False,
            "error": "No knowledge base ID configured",
        }

    try:
        result = knowledge_base_service.start_ingestion_job(
            knowledge_base_id=knowledge_base_id,
            data_source_id=data_source_id,
        )

        metrics.add_metric(name="ScheduledSyncStarted", unit="Count", value=1)

        return {
            "success": True,
            "jobId": result.get("ingestionJobId"),
            "knowledgeBaseId": knowledge_base_id,
        }

    except KnowledgeBaseError as e:
        logger.error("Sync failed", error=e.message)
        metrics.add_metric(name="ScheduledSyncFailed", unit="Count", value=1)
        return {
            "success": False,
            "error": e.message,
        }


@tracer.capture_method
def process_status_check(event: dict[str, Any]) -> dict[str, Any]:
    """Check the status of an ingestion job."""
    knowledge_base_id = event.get("knowledgeBaseId", settings.knowledge_base_id)
    data_source_id = event.get("dataSourceId", settings.knowledge_base_data_source_id)
    job_id = event.get("jobId")

    if not job_id:
        # Get latest job status
        jobs = knowledge_base_service.list_ingestion_jobs(
            knowledge_base_id=knowledge_base_id,
            data_source_id=data_source_id,
            max_results=1,
        )
        if jobs:
            return {
                "success": True,
                "latestJob": jobs[0],
            }
        return {
            "success": True,
            "latestJob": None,
            "message": "No ingestion jobs found",
        }

    # Get specific job status
    status = knowledge_base_service.get_ingestion_job_status(
        knowledge_base_id=knowledge_base_id,
        data_source_id=data_source_id,
        job_id=job_id,
    )

    return {
        "success": True,
        "job": status,
    }


@tracer.capture_method
def process_direct_invocation(event: dict[str, Any]) -> dict[str, Any]:
    """Process direct Lambda invocation for sync operations."""
    action = event.get("action", "sync")

    try:
        if action == "sync":
            knowledge_base_id = event.get("knowledgeBaseId", settings.knowledge_base_id)
            data_source_id = event.get("dataSourceId", settings.knowledge_base_data_source_id)

            result = knowledge_base_service.start_ingestion_job(
                knowledge_base_id=knowledge_base_id,
                data_source_id=data_source_id,
            )

            metrics.add_metric(name="ManualSyncStarted", unit="Count", value=1)

            return ApiResponse(
                success=True,
                data={
                    "jobId": result.get("ingestionJobId"),
                    "knowledgeBaseId": knowledge_base_id,
                    "status": "STARTED",
                },
            ).model_dump(by_alias=True)

        elif action == "status":
            return process_status_check(event)

        elif action == "list-jobs":
            knowledge_base_id = event.get("knowledgeBaseId", settings.knowledge_base_id)
            data_source_id = event.get("dataSourceId", settings.knowledge_base_data_source_id)
            max_results = event.get("maxResults", 10)

            jobs = knowledge_base_service.list_ingestion_jobs(
                knowledge_base_id=knowledge_base_id,
                data_source_id=data_source_id,
                max_results=max_results,
            )

            return ApiResponse(
                success=True,
                data={"jobs": jobs},
            ).model_dump(by_alias=True)

        else:
            return ApiResponse(
                success=False,
                error=f"Unknown action: {action}",
                error_code="INVALID_ACTION",
            ).model_dump(by_alias=True)

    except KnowledgeBaseError as e:
        logger.error("Operation failed", action=action, error=e.message)
        return ApiResponse(
            success=False,
            error=e.message,
            error_code=e.error_code,
        ).model_dump(by_alias=True)

    except Exception as e:
        logger.exception("Unexpected error")
        return ApiResponse(
            success=False,
            error=str(e),
            error_code="INTERNAL_ERROR",
        ).model_dump(by_alias=True)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for knowledge base synchronization.

    Supports:
    - EventBridge scheduled events
    - Direct Lambda invocation with action parameter
    """
    # Check if this is an EventBridge scheduled event
    if event.get("source") == "aws.events" or "detail-type" in event:
        return process_scheduled_sync(event)

    # Direct invocation
    return process_direct_invocation(event)
