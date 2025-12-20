"""Workflow orchestration handlers for Step Functions."""

import time
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.models import (
    DocumentStatus,
    DocumentType,
    ProcessingResult,
)
from src.services.document_service import DocumentService
from src.services.notification_service import NotificationService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Main workflow orchestration handler.

    Routes to appropriate sub-handler based on event type.
    """
    handler_type = event.get("handler_type", "route")

    handlers = {
        "route": route_handler,
        "aggregate": aggregate_handler,
        "finalize": finalize_handler,
        "validate": validate_handler,
    }

    handler_func = handlers.get(handler_type, route_handler)
    return handler_func(event, context)


def validate_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Validate document before processing."""
    document_id = event.get("document_id")
    bucket = event.get("bucket")
    key = event.get("key")
    document_type = event.get("document_type", "UNKNOWN")

    logger.info(
        "Validating document",
        document_id=document_id,
        document_type=document_type,
    )

    doc_service = DocumentService()

    # Get document from DynamoDB
    document = doc_service.get_document(document_id)

    if not document:
        raise ValueError(f"Document not found: {document_id}")

    # Validate document type is supported
    supported_types = [
        DocumentType.PDF.value,
        DocumentType.IMAGE.value,
        DocumentType.AUDIO.value,
        DocumentType.TEXT.value,
    ]

    if document_type not in supported_types:
        raise ValueError(f"Unsupported document type: {document_type}")

    # Validate file exists in S3 (already checked in ingestion, but double-check)
    from src.common.clients import get_clients

    clients = get_clients()
    try:
        clients.s3.head_object(Bucket=bucket, Key=key)
    except Exception as e:
        raise ValueError(f"Document not found in S3: {e}")

    logger.info("Document validated", document_id=document_id)

    return {
        "document_id": document_id,
        "bucket": bucket,
        "key": key,
        "document_type": document_type,
        "status": "validated",
    }


def route_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Route document to appropriate processing path based on type."""
    document_id = event.get("document_id")
    document_type = event.get("document_type", "UNKNOWN")

    logger.info(
        "Routing document",
        document_id=document_id,
        document_type=document_type,
    )

    # Determine processing path
    if document_type == DocumentType.AUDIO.value:
        processing_path = "audio"
    elif document_type == DocumentType.IMAGE.value:
        processing_path = "image"
    elif document_type in [DocumentType.PDF.value, DocumentType.TEXT.value]:
        processing_path = "text"
    else:
        processing_path = "unknown"

    return {
        **event,
        "processing_path": processing_path,
        "status": "routed",
    }


def aggregate_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Aggregate results from parallel processing branches."""
    document_id = event.get("document_id")

    logger.info("Aggregating results", document_id=document_id)

    # Event may contain results from parallel branches
    # Step Functions Parallel state outputs an array
    if isinstance(event, list):
        # Merge results from parallel branches
        aggregated = {"document_id": document_id}
        for branch_result in event:
            if isinstance(branch_result, dict):
                aggregated.update(branch_result)
        return aggregated

    # Single branch result
    return event


def finalize_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Finalize processing and send notifications."""
    document_id = event.get("document_id")
    extraction = event.get("extraction", {})
    analysis = event.get("analysis", {})
    inference = event.get("inference", {})
    generation = event.get("generation", {})
    start_time = event.get("start_time", time.time())

    logger.info("Finalizing document processing", document_id=document_id)

    doc_service = DocumentService()
    notification_service = NotificationService()

    try:
        # Calculate processing time
        processing_time_ms = (time.time() - start_time) * 1000

        # Get document
        document = doc_service.get_document(document_id)

        if not document:
            raise ValueError(f"Document not found: {document_id}")

        # Build processing result
        from src.common.models import (
            AnalysisResult,
            ExtractionResult,
            GenerativeResult,
            InferenceResult,
        )

        result = ProcessingResult(
            document_id=document_id,
            document=document,
            extraction=ExtractionResult(**extraction) if extraction else None,
            analysis=AnalysisResult(document_id=document_id, **analysis) if analysis else None,
            inference=InferenceResult(document_id=document_id, **inference) if inference else None,
            generation=GenerativeResult(document_id=document_id, **generation) if generation else None,
            processing_time_ms=processing_time_ms,
        )

        # Update document status to completed
        doc_service.update_status(document_id, DocumentStatus.COMPLETED)

        # Send success notification
        notification_service.notify_success(document, result)

        logger.info(
            "Document processing completed",
            document_id=document_id,
            processing_time_ms=processing_time_ms,
        )

        return {
            "document_id": document_id,
            "status": "completed",
            "processing_time_ms": processing_time_ms,
            "summary": {
                "words_extracted": extraction.get("words", 0),
                "entities_found": analysis.get("entities", 0),
                "classification": inference.get("predicted_class"),
                "has_summary": bool(generation.get("summary")),
            },
        }

    except Exception as e:
        logger.exception("Finalization failed", document_id=document_id)

        # Update status to failed
        doc_service.update_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=str(e),
        )

        # Get document for notification
        document = doc_service.get_document(document_id)
        if document:
            notification_service.notify_failure(document, str(e))

        raise
