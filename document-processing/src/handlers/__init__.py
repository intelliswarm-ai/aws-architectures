"""Lambda handlers for document processing pipeline."""

from .bedrock_generation import handler as bedrock_handler
from .content_analysis import handler as analysis_handler
from .document_ingestion import handler as ingestion_handler
from .notification import handler as notification_handler
from .sagemaker_inference import handler as inference_handler
from .text_extraction import handler as extraction_handler
from .training_pipeline import handler as training_handler
from .workflow_orchestration import handler as workflow_handler

__all__ = [
    "ingestion_handler",
    "extraction_handler",
    "analysis_handler",
    "inference_handler",
    "bedrock_handler",
    "workflow_handler",
    "training_handler",
    "notification_handler",
]
