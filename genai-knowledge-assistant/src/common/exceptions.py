"""Custom exception hierarchy for the GenAI Knowledge Assistant."""

from typing import Any


class BaseError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.message,
            "errorCode": self.error_code,
            "details": self.details,
        }


# =============================================================================
# Retryable Errors (Transient Failures)
# =============================================================================


class RetryableError(BaseError):
    """Base class for transient errors that can be retried."""

    def __init__(
        self,
        message: str,
        error_code: str = "RETRYABLE_ERROR",
        details: dict[str, Any] | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(message, error_code, details)
        self.retry_after = retry_after


class ServiceUnavailableError(RetryableError):
    """Raised when an AWS service is temporarily unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        service: str | None = None,
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            details={"service": service} if service else {},
            retry_after=retry_after,
        )


class ThrottlingError(RetryableError):
    """Raised when API rate limits are exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        service: str | None = None,
        retry_after: int = 60,
    ) -> None:
        super().__init__(
            message=message,
            error_code="THROTTLING",
            details={"service": service} if service else {},
            retry_after=retry_after,
        )


class BedrockThrottlingError(ThrottlingError):
    """Raised when Bedrock API rate limits are exceeded."""

    def __init__(
        self,
        message: str = "Bedrock API rate limit exceeded",
        model_id: str | None = None,
        retry_after: int = 60,
    ) -> None:
        super().__init__(
            message=message,
            service="bedrock",
            retry_after=retry_after,
        )
        if model_id:
            self.details["modelId"] = model_id


class DatabaseError(RetryableError):
    """Raised for transient database errors."""

    def __init__(
        self,
        message: str = "Database operation failed",
        table: str | None = None,
        operation: str | None = None,
    ) -> None:
        details = {}
        if table:
            details["table"] = table
        if operation:
            details["operation"] = operation
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
        )


class OpenSearchError(RetryableError):
    """Raised for OpenSearch operation errors."""

    def __init__(
        self,
        message: str = "OpenSearch operation failed",
        index: str | None = None,
        operation: str | None = None,
    ) -> None:
        details = {}
        if index:
            details["index"] = index
        if operation:
            details["operation"] = operation
        super().__init__(
            message=message,
            error_code="OPENSEARCH_ERROR",
            details=details,
        )


# =============================================================================
# Non-Retryable Errors (Permanent Failures)
# =============================================================================


class NonRetryableError(BaseError):
    """Base class for permanent errors that should not be retried."""

    pass


class ValidationError(NonRetryableError):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str = "Validation failed",
        field: str | None = None,
        value: Any = None,
    ) -> None:
        details = {}
        if field:
            details["field"] = field
        if value is not None:
            details["value"] = str(value)[:100]  # Truncate for safety
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
        )


class ResourceNotFoundError(NonRetryableError):
    """Raised when a requested resource does not exist."""

    def __init__(
        self,
        message: str = "Resource not found",
        resource_type: str | None = None,
        resource_id: str | None = None,
    ) -> None:
        details = {}
        if resource_type:
            details["resourceType"] = resource_type
        if resource_id:
            details["resourceId"] = resource_id
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
        )


class ConfigurationError(NonRetryableError):
    """Raised when there's a configuration issue."""

    def __init__(
        self,
        message: str = "Configuration error",
        config_key: str | None = None,
    ) -> None:
        details = {}
        if config_key:
            details["configKey"] = config_key
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
        )


class AuthenticationError(NonRetryableError):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication failed",
    ) -> None:
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationError(NonRetryableError):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "Not authorized to perform this action",
        resource: str | None = None,
        action: str | None = None,
    ) -> None:
        details = {}
        if resource:
            details["resource"] = resource
        if action:
            details["action"] = action
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
        )


# =============================================================================
# Knowledge Base Specific Errors
# =============================================================================


class KnowledgeBaseError(NonRetryableError):
    """Raised for knowledge base operation errors."""

    def __init__(
        self,
        message: str = "Knowledge base operation failed",
        knowledge_base_id: str | None = None,
        operation: str | None = None,
    ) -> None:
        details = {}
        if knowledge_base_id:
            details["knowledgeBaseId"] = knowledge_base_id
        if operation:
            details["operation"] = operation
        super().__init__(
            message=message,
            error_code="KNOWLEDGE_BASE_ERROR",
            details=details,
        )


class DocumentIngestionError(NonRetryableError):
    """Raised when document ingestion fails."""

    def __init__(
        self,
        message: str = "Document ingestion failed",
        document_id: str | None = None,
        source_uri: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if document_id:
            details["documentId"] = document_id
        if source_uri:
            details["sourceUri"] = source_uri
        if reason:
            details["reason"] = reason
        super().__init__(
            message=message,
            error_code="DOCUMENT_INGESTION_ERROR",
            details=details,
        )


class EmbeddingError(NonRetryableError):
    """Raised when embedding generation fails."""

    def __init__(
        self,
        message: str = "Embedding generation failed",
        model_id: str | None = None,
        text_length: int | None = None,
    ) -> None:
        details = {}
        if model_id:
            details["modelId"] = model_id
        if text_length:
            details["textLength"] = text_length
        super().__init__(
            message=message,
            error_code="EMBEDDING_ERROR",
            details=details,
        )


class QueryError(NonRetryableError):
    """Raised when a query operation fails."""

    def __init__(
        self,
        message: str = "Query failed",
        query: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if query:
            details["query"] = query[:200]  # Truncate for safety
        if reason:
            details["reason"] = reason
        super().__init__(
            message=message,
            error_code="QUERY_ERROR",
            details=details,
        )


class AgentError(NonRetryableError):
    """Raised when agent invocation fails."""

    def __init__(
        self,
        message: str = "Agent invocation failed",
        agent_id: str | None = None,
        session_id: str | None = None,
        reason: str | None = None,
    ) -> None:
        details = {}
        if agent_id:
            details["agentId"] = agent_id
        if session_id:
            details["sessionId"] = session_id
        if reason:
            details["reason"] = reason
        super().__init__(
            message=message,
            error_code="AGENT_ERROR",
            details=details,
        )


class ContentFilterError(NonRetryableError):
    """Raised when content is blocked by Bedrock guardrails."""

    def __init__(
        self,
        message: str = "Content blocked by guardrails",
        filter_type: str | None = None,
    ) -> None:
        details = {}
        if filter_type:
            details["filterType"] = filter_type
        super().__init__(
            message=message,
            error_code="CONTENT_FILTERED",
            details=details,
        )
