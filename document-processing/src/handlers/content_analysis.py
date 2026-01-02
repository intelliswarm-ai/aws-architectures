"""Content analysis handler - uses Comprehend and Rekognition."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.models import AnalysisResult, DocumentStatus, DocumentType
from src.services.comprehend_service import ComprehendService
from src.services.document_service import DocumentService
from src.services.rekognition_service import RekognitionService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Analyze document content using Comprehend and Rekognition.

    Called by Step Functions workflow after text extraction.
    Performs NLP analysis on text and image analysis for images.
    """
    document_id = event.get("document_id")
    bucket = event.get("bucket")
    key = event.get("key")
    document_type = event.get("document_type", "UNKNOWN")
    extraction = event.get("extraction", {})
    extracted_text = extraction.get("text", "")

    logger.info(
        "Starting content analysis",
        document_id=document_id,
        document_type=document_type,
        text_length=len(extracted_text),
    )

    doc_service = DocumentService()
    comprehend_service = ComprehendService()
    rekognition_service = RekognitionService()

    # Update status
    doc_service.update_status(document_id, DocumentStatus.ANALYZING)

    try:
        # Initialize combined result
        combined_result = AnalysisResult(document_id=document_id)

        # NLP analysis if we have text
        if extracted_text:
            comprehend_result = comprehend_service.analyze_text(
                text=extracted_text,
                document_id=document_id,
                detect_pii=True,
            )

            # Merge Comprehend results
            combined_result.entities = comprehend_result.entities
            combined_result.key_phrases = comprehend_result.key_phrases
            combined_result.sentiment = comprehend_result.sentiment
            combined_result.language = comprehend_result.language
            combined_result.pii_entities = comprehend_result.pii_entities

            logger.info(
                "Comprehend analysis complete",
                document_id=document_id,
                entities=len(combined_result.entities),
                key_phrases=len(combined_result.key_phrases),
                sentiment=combined_result.sentiment.sentiment if combined_result.sentiment else None,
            )

        # Image analysis for images
        if document_type == DocumentType.IMAGE.value:
            rekognition_result = rekognition_service.analyze_image(
                bucket=bucket,
                key=key,
                document_id=document_id,
                detect_moderation=True,
            )

            # Merge Rekognition results
            combined_result.image_labels = rekognition_result.image_labels
            combined_result.detected_text = rekognition_result.detected_text
            combined_result.moderation_labels = rekognition_result.moderation_labels

            logger.info(
                "Rekognition analysis complete",
                document_id=document_id,
                labels=len(combined_result.image_labels),
                detected_text=len(combined_result.detected_text),
                moderation_labels=len(combined_result.moderation_labels),
            )

        # Save result to document metadata
        doc_service.save_processing_result(
            document_id=document_id,
            result_type="analysis",
            result=combined_result.model_dump(),
        )

        # Update status
        doc_service.update_status(document_id, DocumentStatus.ANALYZED)

        # Prepare response
        response = {
            "document_id": document_id,
            "status": "analyzed",
            "analysis": {
                "entities": len(combined_result.entities),
                "key_phrases": combined_result.key_phrases[:10],  # Top 10
                "sentiment": combined_result.sentiment.sentiment if combined_result.sentiment else None,
                "language": combined_result.language,
                "pii_detected": len(combined_result.pii_entities) > 0,
                "image_labels": [l.name for l in combined_result.image_labels[:10]],
                "moderation_flagged": len(combined_result.moderation_labels) > 0,
            },
            # Pass through for next step
            "extraction": extraction,
        }

        return response

    except Exception as e:
        logger.exception("Content analysis failed", document_id=document_id)
        doc_service.update_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=str(e),
        )
        raise
