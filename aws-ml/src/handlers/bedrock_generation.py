"""Bedrock generation handler - summarization and Q&A."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.models import DocumentStatus
from src.services.bedrock_service import BedrockService
from src.services.document_service import DocumentService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Generate summary and Q&A using Amazon Bedrock.

    Called by Step Functions workflow after classification.
    Uses Claude to generate document insights.
    """
    document_id = event.get("document_id")
    extraction = event.get("extraction", {})
    analysis = event.get("analysis", {})
    inference = event.get("inference", {})
    extracted_text = extraction.get("text", "")

    logger.info(
        "Starting Bedrock generation",
        document_id=document_id,
        text_length=len(extracted_text),
    )

    doc_service = DocumentService()
    bedrock_service = BedrockService()

    # Update status
    doc_service.update_status(document_id, DocumentStatus.GENERATING)

    try:
        if not extracted_text:
            logger.warning("No text available for generation", document_id=document_id)
            return {
                "document_id": document_id,
                "status": "skipped",
                "reason": "No text content",
                "extraction": extraction,
                "analysis": analysis,
                "inference": inference,
            }

        # Perform comprehensive document processing
        result = bedrock_service.process_document(
            document_id=document_id,
            text=extracted_text,
        )

        # Save result to document metadata
        doc_service.save_processing_result(
            document_id=document_id,
            result_type="generation",
            result=result.model_dump(),
        )

        logger.info(
            "Bedrock generation complete",
            document_id=document_id,
            has_summary=bool(result.summary),
            qa_pairs=len(result.questions),
            topics=len(result.topics),
            action_items=len(result.action_items),
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
        )

        return {
            "document_id": document_id,
            "status": "generated",
            "generation": {
                "summary": result.summary[:500] if result.summary else "",  # Truncate for response
                "questions": result.questions[:5],  # First 5 Q&A pairs
                "topics": result.topics[:10],
                "action_items": result.action_items,
                "model_id": result.model_id,
                "tokens": {
                    "input": result.input_tokens,
                    "output": result.output_tokens,
                },
            },
            # Pass through for finalization
            "extraction": extraction,
            "analysis": analysis,
            "inference": inference,
        }

    except Exception as e:
        logger.exception("Bedrock generation failed", document_id=document_id)
        doc_service.update_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=str(e),
        )
        raise


@tracer.capture_method
def summarize_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Dedicated summarization handler (alternative entry point)."""
    document_id = event.get("document_id")
    text = event.get("text", "")
    max_length = event.get("max_length", 500)

    bedrock_service = BedrockService()

    result = bedrock_service.generate_summary(
        document_id=document_id,
        text=text,
        max_length=max_length,
    )

    return {
        "document_id": document_id,
        "summary": result.summary,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }


@tracer.capture_method
def qa_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Dedicated Q&A generation handler (alternative entry point)."""
    document_id = event.get("document_id")
    text = event.get("text", "")
    num_pairs = event.get("num_pairs", 5)

    bedrock_service = BedrockService()

    result = bedrock_service.generate_qa_pairs(
        document_id=document_id,
        text=text,
        num_pairs=num_pairs,
    )

    return {
        "document_id": document_id,
        "questions": result.questions,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }
