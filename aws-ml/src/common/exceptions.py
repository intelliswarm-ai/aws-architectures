"""Custom exceptions for document processing."""


class DocumentProcessingError(Exception):
    """Base exception for document processing errors."""

    def __init__(self, message: str, document_id: str | None = None):
        self.message = message
        self.document_id = document_id
        super().__init__(self.message)


class RetryableError(DocumentProcessingError):
    """Error that can be retried (transient failures)."""

    def __init__(
        self,
        message: str,
        document_id: str | None = None,
        retry_after_seconds: int = 60,
    ):
        super().__init__(message, document_id)
        self.retry_after_seconds = retry_after_seconds


class NonRetryableError(DocumentProcessingError):
    """Error that should not be retried (permanent failures)."""

    pass


class ValidationError(NonRetryableError):
    """Document validation error."""

    def __init__(self, message: str, document_id: str | None = None, field: str | None = None):
        super().__init__(message, document_id)
        self.field = field


class ExtractionError(DocumentProcessingError):
    """Error during text extraction."""

    def __init__(
        self,
        message: str,
        document_id: str | None = None,
        service: str = "textract",
    ):
        super().__init__(message, document_id)
        self.service = service


class InferenceError(DocumentProcessingError):
    """Error during ML inference."""

    def __init__(
        self,
        message: str,
        document_id: str | None = None,
        model_name: str | None = None,
    ):
        super().__init__(message, document_id)
        self.model_name = model_name


class GenerationError(DocumentProcessingError):
    """Error during content generation."""

    def __init__(
        self,
        message: str,
        document_id: str | None = None,
        model_id: str | None = None,
    ):
        super().__init__(message, document_id)
        self.model_id = model_id


class ServiceUnavailableError(RetryableError):
    """AWS service temporarily unavailable."""

    def __init__(
        self,
        message: str,
        service_name: str,
        document_id: str | None = None,
    ):
        super().__init__(message, document_id)
        self.service_name = service_name


class ThrottlingError(RetryableError):
    """Request was throttled by AWS."""

    def __init__(
        self,
        message: str,
        document_id: str | None = None,
        retry_after_seconds: int = 30,
    ):
        super().__init__(message, document_id, retry_after_seconds)


class QuotaExceededError(NonRetryableError):
    """Service quota exceeded."""

    def __init__(
        self,
        message: str,
        quota_name: str,
        document_id: str | None = None,
    ):
        super().__init__(message, document_id)
        self.quota_name = quota_name
