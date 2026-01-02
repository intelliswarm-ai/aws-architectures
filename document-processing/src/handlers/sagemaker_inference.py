"""SageMaker inference handler - document classification."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.models import DocumentStatus
from src.services.document_service import DocumentService
from src.services.sagemaker_service import SageMakerService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Classify document using SageMaker endpoint.

    Called by Step Functions workflow after content analysis.
    Uses extracted features to classify the document.
    """
    document_id = event.get("document_id")
    extraction = event.get("extraction", {})
    analysis = event.get("analysis", {})

    logger.info(
        "Starting SageMaker inference",
        document_id=document_id,
    )

    settings = get_settings()
    doc_service = DocumentService()
    sagemaker_service = SageMakerService()

    # Update status
    doc_service.update_status(document_id, DocumentStatus.CLASSIFYING)

    try:
        # Build feature vector from extraction and analysis results
        features = build_feature_vector(extraction, analysis)

        logger.info(
            "Feature vector built",
            document_id=document_id,
            feature_count=len(features),
        )

        # Check if endpoint is configured
        if not settings.sagemaker_endpoint_name:
            logger.warning("SageMaker endpoint not configured, using mock classification")
            result = mock_classification(document_id, analysis)
        else:
            # Invoke SageMaker endpoint
            result = sagemaker_service.invoke_endpoint(
                document_id=document_id,
                features=features,
            )

        # Save result to document metadata
        doc_service.save_processing_result(
            document_id=document_id,
            result_type="inference",
            result=result.model_dump(),
        )

        # Update status
        doc_service.update_status(document_id, DocumentStatus.CLASSIFIED)

        logger.info(
            "Classification complete",
            document_id=document_id,
            predicted_class=result.predicted_class,
            confidence=result.confidence,
        )

        return {
            "document_id": document_id,
            "status": "classified",
            "inference": {
                "predicted_class": result.predicted_class,
                "confidence": result.confidence,
                "probabilities": result.probabilities,
                "latency_ms": result.latency_ms,
            },
            # Pass through for next step
            "extraction": extraction,
            "analysis": analysis,
        }

    except Exception as e:
        logger.exception("SageMaker inference failed", document_id=document_id)
        doc_service.update_status(
            document_id,
            DocumentStatus.FAILED,
            error_message=str(e),
        )
        raise


def build_feature_vector(
    extraction: dict[str, Any],
    analysis: dict[str, Any],
) -> dict[str, Any]:
    """
    Build feature vector for classification model.

    Features include:
    - Text statistics (word count, page count)
    - Entity counts by type
    - Sentiment scores
    - Key phrase indicators
    - Image label indicators
    """
    features: dict[str, Any] = {
        # Text statistics
        "word_count": extraction.get("words", 0),
        "page_count": extraction.get("pages", 1),
        "extraction_confidence": extraction.get("confidence", 0),
        "has_tables": extraction.get("tables", 0) > 0,
        "has_forms": extraction.get("forms", 0) > 0,
        # Analysis stats
        "entity_count": analysis.get("entities", 0),
        "key_phrase_count": len(analysis.get("key_phrases", [])),
        "has_pii": analysis.get("pii_detected", False),
        "is_moderation_flagged": analysis.get("moderation_flagged", False),
        # Sentiment (if available)
        "sentiment": analysis.get("sentiment", "NEUTRAL"),
        # Language
        "language": analysis.get("language", "en"),
        # Image features
        "image_label_count": len(analysis.get("image_labels", [])),
    }

    # Add key phrases as features (top 5)
    key_phrases = analysis.get("key_phrases", [])
    for i, phrase in enumerate(key_phrases[:5]):
        features[f"key_phrase_{i}"] = phrase

    # Add image labels as features (top 5)
    image_labels = analysis.get("image_labels", [])
    for i, label in enumerate(image_labels[:5]):
        features[f"image_label_{i}"] = label

    return features


def mock_classification(
    document_id: str,
    analysis: dict[str, Any],
) -> Any:
    """Mock classification when endpoint is not available."""
    from src.common.models import InferenceResult

    # Simple rule-based classification for demo
    key_phrases = analysis.get("key_phrases", [])
    sentiment = analysis.get("sentiment", "NEUTRAL")

    # Classify based on keywords
    text = " ".join(key_phrases).lower()

    if any(word in text for word in ["invoice", "payment", "amount", "total"]):
        predicted_class = "INVOICE"
        confidence = 0.85
    elif any(word in text for word in ["contract", "agreement", "terms", "party"]):
        predicted_class = "CONTRACT"
        confidence = 0.82
    elif any(word in text for word in ["report", "analysis", "findings", "summary"]):
        predicted_class = "REPORT"
        confidence = 0.78
    elif any(word in text for word in ["resume", "experience", "skills", "education"]):
        predicted_class = "RESUME"
        confidence = 0.80
    else:
        predicted_class = "OTHER"
        confidence = 0.60

    return InferenceResult(
        document_id=document_id,
        predicted_class=predicted_class,
        confidence=confidence,
        probabilities={
            "INVOICE": 0.1,
            "CONTRACT": 0.1,
            "REPORT": 0.1,
            "RESUME": 0.1,
            "OTHER": 0.6,
            predicted_class: confidence,
        },
        model_version="mock-v1",
        latency_ms=5.0,
    )
