"""Custom exceptions for the ML transformation pipeline."""

from typing import Any


class BaseTransformationError(Exception):
    """Base exception for all transformation errors."""

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the exception.

        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional context about the error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "TRANSFORMATION_ERROR"
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging."""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }


class ConfigurationError(BaseTransformationError):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self,
        message: str,
        config_key: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details={"config_key": config_key, **(details or {})},
        )
        self.config_key = config_key


class PIITokenizationError(BaseTransformationError):
    """Raised when PII tokenization fails."""

    def __init__(
        self,
        message: str,
        column_name: str | None = None,
        record_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="PII_TOKENIZATION_ERROR",
            details={
                "column_name": column_name,
                "record_id": record_id,
                **(details or {}),
            },
        )
        self.column_name = column_name
        self.record_id = record_id


class TransformationError(BaseTransformationError):
    """Raised when a data transformation fails."""

    def __init__(
        self,
        message: str,
        transformation_type: str | None = None,
        record_count: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="TRANSFORMATION_ERROR",
            details={
                "transformation_type": transformation_type,
                "record_count": record_count,
                **(details or {}),
            },
        )
        self.transformation_type = transformation_type
        self.record_count = record_count


class DataQualityError(BaseTransformationError):
    """Raised when data quality checks fail."""

    def __init__(
        self,
        message: str,
        check_name: str | None = None,
        threshold: float | None = None,
        actual_value: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="DATA_QUALITY_ERROR",
            details={
                "check_name": check_name,
                "threshold": threshold,
                "actual_value": actual_value,
                **(details or {}),
            },
        )
        self.check_name = check_name
        self.threshold = threshold
        self.actual_value = actual_value


class LineageError(BaseTransformationError):
    """Raised when lineage tracking fails."""

    def __init__(
        self,
        message: str,
        job_execution_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="LINEAGE_ERROR",
            details={"job_execution_id": job_execution_id, **(details or {})},
        )
        self.job_execution_id = job_execution_id


class AuditError(BaseTransformationError):
    """Raised when audit logging fails."""

    def __init__(
        self,
        message: str,
        event_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="AUDIT_ERROR",
            details={"event_type": event_type, **(details or {})},
        )
        self.event_type = event_type


class GlueJobError(BaseTransformationError):
    """Raised when Glue job execution fails."""

    def __init__(
        self,
        message: str,
        job_name: str | None = None,
        job_run_id: str | None = None,
        error_message: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="GLUE_JOB_ERROR",
            details={
                "job_name": job_name,
                "job_run_id": job_run_id,
                "error_message": error_message,
                **(details or {}),
            },
        )
        self.job_name = job_name
        self.job_run_id = job_run_id
        self.error_message = error_message
