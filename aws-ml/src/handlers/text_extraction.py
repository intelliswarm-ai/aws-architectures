"""Text extraction handler - uses Textract for PDFs/images."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.models import DocumentStatus, DocumentType
from src.services.document_service import DocumentService
from src.services.textract_service import TextractService

logger = Logger()
tracer = Tracer()

# Size threshold for async processing (5MB)
ASYNC_SIZE_THRESHOLD = 5 * 1024 * 1024


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Extract text from document using Amazon Textract.

    Called by Step Functions workflow.
    Uses sync API for small documents, async API for large ones.
    """
    document_id = event.get("document_id")
    bucket = event.get("bucket")
    key = event.get("key")
    document_type = event.get("document_type", "UNKNOWN")

    logger.info(
        "Starting text extraction",
        document_id=document_id,
        document_type=document_type,
    )

    doc_service = DocumentService()
    textract_service = TextractService()

    # Update status
    doc_service.update_status(document_id, DocumentStatus.EXTRACTING)

    try:
        # Get document to check size
        document = doc_service.get_document(document_id)
        file_size = document.file_size if document else 0

        # Choose extraction method based on size and type
        if document_type == DocumentType.IMAGE.value:
            # For images, use analyze_document for better results
            result = textract_service.analyze_document(
                bucket=bucket,
                key=key,
                document_id=document_id,
                feature_types=["TABLES", "FORMS"],
            )
        elif file_size > ASYNC_SIZE_THRESHOLD:
            # Large documents - use async API
            job_id = textract_service.extract_text_async(
                bucket=bucket,
                key=key,
                document_id=document_id,
            )
            # Wait for completion (Step Functions could handle this with Wait state)
            result = textract_service.get_async_result(
                job_id=job_id,
                document_id=document_id,
                wait=True,
                max_wait_seconds=300,
            )
        else:
            # Small documents - use sync API
            result = textract_service.extract_text_sync(
                bucket=bucket,
                key=key,
                document_id=document_id,
            )

        # Save result to document metadata
        doc_service.save_processing_result(
            document_id=document_id,
            result_type="extraction",
            result=result.model_dump(),
        )

        # Update status
        doc_service.update_status(document_id, DocumentStatus.EXTRACTED)

        logger.info(
            "Text extraction complete",
            document_id=document_id,
            words=result.words,
            pages=result.pages,
            confidence=result.confidence,
        )

        return {
            "document_id": document_id,
            "status": "extracted",
            "extraction": {
                "text": result.extracted_text,
                "words": result.words,
                "pages": result.pages,
                "confidence": result.confidence,
                "tables": len(result.tables),
                "forms": len(result.forms),
            },
        }

    except Exception as e:
        logger.exception("Text extraction failed", document_id=document_id)
        doc_service.update_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=str(e),
        )
        raise
