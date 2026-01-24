"""Custom exceptions for ML Canary Deployment system."""


class MLCanaryDeploymentError(Exception):
    """Base exception for ML Canary Deployment system."""

    def __init__(
        self,
        message: str,
        deployment_id: str | None = None,
        endpoint_name: str | None = None,
        details: dict | None = None,
    ):
        """Initialize exception.

        Args:
            message: Error message.
            deployment_id: Optional deployment identifier.
            endpoint_name: Optional endpoint name.
            details: Optional additional error details.
        """
        super().__init__(message)
        self.message = message
        self.deployment_id = deployment_id
        self.endpoint_name = endpoint_name
        self.details = details or {}

    def to_dict(self) -> dict:
        """Convert exception to dictionary for logging/response."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "deployment_id": self.deployment_id,
            "endpoint_name": self.endpoint_name,
            "details": self.details,
        }


class RetryableError(MLCanaryDeploymentError):
    """Exception for transient errors that should be retried."""

    def __init__(
        self,
        message: str,
        deployment_id: str | None = None,
        endpoint_name: str | None = None,
        retry_after_seconds: int = 60,
        details: dict | None = None,
    ):
        """Initialize retryable exception.

        Args:
            message: Error message.
            deployment_id: Optional deployment identifier.
            endpoint_name: Optional endpoint name.
            retry_after_seconds: Suggested retry delay.
            details: Optional additional error details.
        """
        super().__init__(message, deployment_id, endpoint_name, details)
        self.retry_after_seconds = retry_after_seconds

    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["retry_after_seconds"] = self.retry_after_seconds
        return result


class NonRetryableError(MLCanaryDeploymentError):
    """Exception for permanent errors that should not be retried."""

    pass


class ValidationError(NonRetryableError):
    """Exception for input validation failures."""

    pass


class InferenceError(MLCanaryDeploymentError):
    """Exception for model inference failures."""

    def __init__(
        self,
        message: str,
        variant_name: str | None = None,
        request_id: str | None = None,
        deployment_id: str | None = None,
        endpoint_name: str | None = None,
        details: dict | None = None,
    ):
        """Initialize inference exception.

        Args:
            message: Error message.
            variant_name: Optional variant that failed.
            request_id: Optional request identifier.
            deployment_id: Optional deployment identifier.
            endpoint_name: Optional endpoint name.
            details: Optional additional error details.
        """
        super().__init__(message, deployment_id, endpoint_name, details)
        self.variant_name = variant_name
        self.request_id = request_id

    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["variant_name"] = self.variant_name
        result["request_id"] = self.request_id
        return result


class DeploymentError(MLCanaryDeploymentError):
    """Exception for deployment operation failures."""

    def __init__(
        self,
        message: str,
        deployment_id: str | None = None,
        endpoint_name: str | None = None,
        variant_name: str | None = None,
        details: dict | None = None,
    ):
        """Initialize deployment exception.

        Args:
            message: Error message.
            deployment_id: Optional deployment identifier.
            endpoint_name: Optional endpoint name.
            variant_name: Optional variant name.
            details: Optional additional error details.
        """
        super().__init__(message, deployment_id, endpoint_name, details)
        self.variant_name = variant_name

    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["variant_name"] = self.variant_name
        return result


class TrafficShiftError(MLCanaryDeploymentError):
    """Exception for traffic shifting failures."""

    def __init__(
        self,
        message: str,
        deployment_id: str | None = None,
        endpoint_name: str | None = None,
        current_weights: dict[str, float] | None = None,
        target_weights: dict[str, float] | None = None,
        details: dict | None = None,
    ):
        """Initialize traffic shift exception.

        Args:
            message: Error message.
            deployment_id: Optional deployment identifier.
            endpoint_name: Optional endpoint name.
            current_weights: Current traffic weights.
            target_weights: Target traffic weights.
            details: Optional additional error details.
        """
        super().__init__(message, deployment_id, endpoint_name, details)
        self.current_weights = current_weights or {}
        self.target_weights = target_weights or {}

    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["current_weights"] = self.current_weights
        result["target_weights"] = self.target_weights
        return result


class MonitoringError(MLCanaryDeploymentError):
    """Exception for monitoring and metrics failures."""

    def __init__(
        self,
        message: str,
        deployment_id: str | None = None,
        endpoint_name: str | None = None,
        metric_name: str | None = None,
        details: dict | None = None,
    ):
        """Initialize monitoring exception.

        Args:
            message: Error message.
            deployment_id: Optional deployment identifier.
            endpoint_name: Optional endpoint name.
            metric_name: Optional metric that failed.
            details: Optional additional error details.
        """
        super().__init__(message, deployment_id, endpoint_name, details)
        self.metric_name = metric_name

    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["metric_name"] = self.metric_name
        return result


class RollbackError(MLCanaryDeploymentError):
    """Exception for rollback operation failures."""

    pass


class EndpointNotFoundError(NonRetryableError):
    """Exception when endpoint does not exist."""

    pass


class VariantNotFoundError(NonRetryableError):
    """Exception when variant does not exist."""

    pass


class ModelNotFoundError(NonRetryableError):
    """Exception when model does not exist."""

    pass


class ServiceUnavailableError(RetryableError):
    """Exception when AWS service is temporarily unavailable."""

    def __init__(
        self,
        message: str,
        service_name: str,
        deployment_id: str | None = None,
        endpoint_name: str | None = None,
        retry_after_seconds: int = 60,
        details: dict | None = None,
    ):
        """Initialize service unavailable exception.

        Args:
            message: Error message.
            service_name: AWS service that is unavailable.
            deployment_id: Optional deployment identifier.
            endpoint_name: Optional endpoint name.
            retry_after_seconds: Suggested retry delay.
            details: Optional additional error details.
        """
        super().__init__(
            message, deployment_id, endpoint_name, retry_after_seconds, details
        )
        self.service_name = service_name

    def to_dict(self) -> dict:
        """Convert exception to dictionary."""
        result = super().to_dict()
        result["service_name"] = self.service_name
        return result


class ThrottlingError(RetryableError):
    """Exception for API throttling."""

    def __init__(
        self,
        message: str,
        deployment_id: str | None = None,
        endpoint_name: str | None = None,
        retry_after_seconds: int = 30,
        details: dict | None = None,
    ):
        """Initialize throttling exception with shorter default retry."""
        super().__init__(
            message, deployment_id, endpoint_name, retry_after_seconds, details
        )
