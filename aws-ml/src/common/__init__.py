"""Common module with shared models, utilities, and AWS clients."""

from .clients import get_bedrock_client, get_clients
from .config import Settings, get_settings
from .exceptions import (
    DocumentProcessingError,
    ExtractionError,
    GenerationError,
    InferenceError,
    NonRetryableError,
    RetryableError,
    ValidationError,
)
from .models import (
    AnalysisResult,
    Document,
    DocumentStatus,
    DocumentType,
    ExtractionResult,
    GenerativeResult,
    InferenceResult,
    ProcessingResult,
)

__all__ = [
    # Models
    "Document",
    "DocumentStatus",
    "DocumentType",
    "ProcessingResult",
    "ExtractionResult",
    "AnalysisResult",
    "InferenceResult",
    "GenerativeResult",
    # Exceptions
    "DocumentProcessingError",
    "RetryableError",
    "NonRetryableError",
    "ExtractionError",
    "InferenceError",
    "GenerationError",
    "ValidationError",
    # Clients
    "get_clients",
    "get_bedrock_client",
    # Config
    "Settings",
    "get_settings",
]
