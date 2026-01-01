"""Custom exceptions for call sentiment analysis."""


class CallSentimentError(Exception):
    """Base exception for call sentiment analysis."""

    def __init__(self, message: str, details: dict | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class TranscriptParseError(CallSentimentError):
    """Error parsing transcript file."""

    def __init__(self, message: str, file_key: str | None = None):
        super().__init__(message, {"file_key": file_key})
        self.file_key = file_key


class ComprehendError(CallSentimentError):
    """Error with Amazon Comprehend operations."""

    def __init__(
        self,
        message: str,
        job_id: str | None = None,
        operation: str | None = None,
    ):
        super().__init__(message, {"job_id": job_id, "operation": operation})
        self.job_id = job_id
        self.operation = operation


class OpenSearchError(CallSentimentError):
    """Error with OpenSearch operations."""

    def __init__(
        self,
        message: str,
        index: str | None = None,
        operation: str | None = None,
    ):
        super().__init__(message, {"index": index, "operation": operation})
        self.index = index
        self.operation = operation


class ValidationError(CallSentimentError):
    """Validation error for input data."""

    def __init__(self, message: str, field: str | None = None):
        super().__init__(message, {"field": field})
        self.field = field
