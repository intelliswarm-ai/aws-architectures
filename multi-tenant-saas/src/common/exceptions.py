"""Custom exceptions for the enterprise serverless platform."""

from typing import Any


class BaseError(Exception):
    """Base exception for all custom errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class RetryableError(BaseError):
    """Error that can be retried (transient failures)."""

    pass


class NonRetryableError(BaseError):
    """Error that should not be retried (permanent failures)."""

    pass


class ConfigurationError(NonRetryableError):
    """Configuration or environment error."""

    pass


class ValidationError(NonRetryableError):
    """Request validation error."""

    def __init__(
        self,
        message: str = "Validation failed",
        field_errors: dict[str, str] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details={"field_errors": field_errors or {}},
        )
        self.field_errors = field_errors or {}


class AuthenticationError(NonRetryableError):
    """Authentication failure (invalid/missing credentials)."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
        )


class AuthorizationError(NonRetryableError):
    """Authorization failure (insufficient permissions)."""

    def __init__(
        self,
        message: str = "Access denied",
        required_permission: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details={"required_permission": required_permission} if required_permission else {},
        )


class ResourceNotFoundError(NonRetryableError):
    """Requested resource not found."""

    def __init__(
        self,
        resource_type: str,
        resource_id: str,
    ) -> None:
        super().__init__(
            message=f"{resource_type} not found: {resource_id}",
            error_code="RESOURCE_NOT_FOUND",
            details={"resource_type": resource_type, "resource_id": resource_id},
        )


class TenantError(NonRetryableError):
    """Tenant-related error (invalid tenant, suspended, etc.)."""

    def __init__(
        self,
        message: str,
        tenant_id: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="TENANT_ERROR",
            details={"tenant_id": tenant_id} if tenant_id else {},
        )


class RateLimitError(NonRetryableError):
    """Rate limit exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            details={"retry_after_seconds": retry_after} if retry_after else {},
        )


class ExternalServiceError(RetryableError):
    """External service (AWS, third-party API) error."""

    def __init__(
        self,
        service: str,
        message: str,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"{service}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={
                "service": service,
                "original_error": str(original_error) if original_error else None,
            },
        )


class DatabaseError(RetryableError):
    """Database operation error."""

    def __init__(
        self,
        operation: str,
        message: str,
        original_error: Exception | None = None,
    ) -> None:
        super().__init__(
            message=f"Database {operation} failed: {message}",
            error_code="DATABASE_ERROR",
            details={
                "operation": operation,
                "original_error": str(original_error) if original_error else None,
            },
        )


class SecretsError(RetryableError):
    """Secrets Manager operation error."""

    def __init__(
        self,
        secret_id: str,
        message: str,
    ) -> None:
        super().__init__(
            message=f"Secret operation failed for {secret_id}: {message}",
            error_code="SECRETS_ERROR",
            details={"secret_id": secret_id},
        )
