"""Document ingestion handler for S3 events and direct invocations."""

import json
import urllib.parse
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes import S3Event, SQSEvent
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.exceptions import DocumentIngestionError
from src.common.models import (
    ApiResponse,
    DocumentStatus,
    IngestionRequest,
    IngestionResponse,
    SourceType,
)
from src.services.document_service import DocumentService

logger = Logger()
tracer = Tracer()
metrics = Metrics()
processor = BatchProcessor(event_type=EventType.SQS)

settings = get_settings()
document_service = DocumentService()


@tracer.capture_method
def process_s3_record(record: dict[str, Any]) -> IngestionResponse:
    """Process a single S3 event record."""
    bucket = record["s3"]["bucket"]["name"]
    key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
    size = record["s3"]["object"].get("size", 0)

    logger.info(
        "Processing S3 object",
        bucket=bucket,
        key=key,
        size=size,
    )

    # Skip folders and empty objects
    if key.endswith("/") or size == 0:
        logger.info("Skipping folder or empty object", key=key)
        return IngestionResponse(
            document_id="",
            status=DocumentStatus.PENDING,
            message="Skipped: folder or empty object",
        )

    # Build S3 URI
    source_uri = f"s3://{bucket}/{key}"

    # Create ingestion request
    request = IngestionRequest(
        source_uri=source_uri,
        source_type=SourceType.S3,
        knowledge_base_id=settings.knowledge_base_id,
    )

    response = document_service.ingest(request)

    metrics.add_metric(name="S3DocumentsIngested", unit="Count", value=1)
    metrics.add_metric(name="DocumentSizeBytes", unit="Bytes", value=size)

    return response


@tracer.capture_method
def process_sqs_record(record: SQSRecord) -> IngestionResponse:
    """Process a single SQS record containing ingestion request."""
    body = json.loads(record.body)

    # Handle S3 event notifications via SQS
    if "Records" in body:
        # This is an S3 event wrapped in SQS
        s3_record = body["Records"][0]
        return process_s3_record(s3_record)

    # Handle SNS-wrapped messages
    if "Message" in body:
        body = json.loads(body["Message"])
        if "Records" in body:
            s3_record = body["Records"][0]
            return process_s3_record(s3_record)

    # Direct ingestion request
    request = IngestionRequest(**body)

    logger.info(
        "Processing ingestion request from SQS",
        source_uri=request.source_uri,
        message_id=record.message_id,
    )

    response = document_service.ingest(request)

    metrics.add_metric(name="SQSDocumentsIngested", unit="Count", value=1)

    return response


@tracer.capture_method
def process_s3_event(event: dict[str, Any]) -> dict[str, Any]:
    """Process direct S3 event."""
    s3_event = S3Event(event)
    results = []

    for record in s3_event.records:
        try:
            result = process_s3_record(record.raw_event)
            results.append(result.model_dump(by_alias=True))
        except DocumentIngestionError as e:
            logger.error("Ingestion failed", error=e.message, details=e.details)
            results.append({
                "status": "failed",
                "error": e.message,
            })
        except Exception as e:
            logger.exception("Unexpected error processing S3 record")
            results.append({
                "status": "failed",
                "error": str(e),
            })

    return {
        "processed": len(results),
        "results": results,
    }


@tracer.capture_method
def process_direct_invocation(event: dict[str, Any]) -> dict[str, Any]:
    """Process direct Lambda invocation for ingestion."""
    try:
        request = IngestionRequest(**event)

        logger.info(
            "Processing direct ingestion invocation",
            source_uri=request.source_uri,
        )

        response = document_service.ingest(request)

        metrics.add_metric(name="DirectDocumentsIngested", unit="Count", value=1)

        return ApiResponse(
            success=True,
            data=response.model_dump(by_alias=True),
        ).model_dump(by_alias=True)

    except DocumentIngestionError as e:
        logger.error("Ingestion failed", error=e.message)
        return ApiResponse(
            success=False,
            error=e.message,
            error_code=e.error_code,
        ).model_dump(by_alias=True)

    except Exception as e:
        logger.exception("Unexpected error during ingestion")
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
    Lambda handler for document ingestion.

    Supports:
    - S3 event notifications (direct)
    - SQS batch processing (S3 via SQS or direct requests)
    - Direct Lambda invocation
    """
    # Check if this is an SQS event
    if "Records" in event and event["Records"][0].get("eventSource") == "aws:sqs":
        logger.info("Processing SQS batch", record_count=len(event["Records"]))
        return process_partial_response(
            event=event,
            record_handler=process_sqs_record,
            processor=processor,
            context=context,
        )

    # Check if this is an S3 event
    if "Records" in event and event["Records"][0].get("eventSource") == "aws:s3":
        logger.info("Processing S3 event", record_count=len(event["Records"]))
        return process_s3_event(event)

    # Direct invocation
    return process_direct_invocation(event)
