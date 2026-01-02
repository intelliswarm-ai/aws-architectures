"""Audio transcription handler - uses Transcribe for audio files."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.models import DocumentStatus
from src.services.document_service import DocumentService
from src.services.transcribe_service import TranscribeService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Transcribe audio document using Amazon Transcribe.

    Called by Step Functions workflow for audio documents.
    Starts async job and waits for completion.
    """
    document_id = event.get("document_id")
    bucket = event.get("bucket")
    key = event.get("key")
    language_code = event.get("language_code", "en-US")

    logger.info(
        "Starting audio transcription",
        document_id=document_id,
        language_code=language_code,
    )

    doc_service = DocumentService()
    transcribe_service = TranscribeService()

    # Update status
    doc_service.update_status(document_id, DocumentStatus.EXTRACTING)

    try:
        # Start transcription job
        job_name = transcribe_service.start_transcription(
            bucket=bucket,
            key=key,
            document_id=document_id,
            language_code=language_code,
        )

        logger.info(
            "Transcription job started",
            document_id=document_id,
            job_name=job_name,
        )

        # Wait for completion
        result = transcribe_service.get_transcription_result(
            job_name=job_name,
            document_id=document_id,
            wait=True,
            max_wait_seconds=600,
        )

        if result is None:
            raise Exception("Transcription did not complete in time")

        # Clean up transcription job
        transcribe_service.delete_transcription_job(job_name)

        # Save result to document metadata
        doc_service.save_processing_result(
            document_id=document_id,
            result_type="extraction",
            result=result.model_dump(),
        )

        # Update status
        doc_service.update_status(document_id, DocumentStatus.EXTRACTED)

        logger.info(
            "Transcription complete",
            document_id=document_id,
            words=result.words,
            confidence=result.confidence,
        )

        return {
            "document_id": document_id,
            "status": "extracted",
            "extraction": {
                "text": result.extracted_text,
                "words": result.words,
                "confidence": result.confidence,
                "language": result.language or language_code,
            },
        }

    except Exception as e:
        logger.exception("Transcription failed", document_id=document_id)
        doc_service.update_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=str(e),
        )
        raise
