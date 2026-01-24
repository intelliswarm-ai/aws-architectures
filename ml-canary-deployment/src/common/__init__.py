"""Common utilities, models, and configuration for ML Canary Deployment."""

from src.common.clients import AWSClients, get_clients
from src.common.config import Settings, get_settings
from src.common.exceptions import (
    DeploymentError,
    InferenceError,
    MLCanaryDeploymentError,
    MonitoringError,
    NonRetryableError,
    RetryableError,
    TrafficShiftError,
    ValidationError,
)
from src.common.models import (
    DeploymentConfig,
    DeploymentStatus,
    EndpointMetrics,
    InferenceRequest,
    InferenceResponse,
    ModelVariant,
    TrafficConfig,
    VariantStatus,
)

__all__ = [
    # Clients
    "AWSClients",
    "get_clients",
    # Config
    "Settings",
    "get_settings",
    # Exceptions
    "MLCanaryDeploymentError",
    "RetryableError",
    "NonRetryableError",
    "ValidationError",
    "InferenceError",
    "DeploymentError",
    "TrafficShiftError",
    "MonitoringError",
    # Models
    "InferenceRequest",
    "InferenceResponse",
    "ModelVariant",
    "DeploymentConfig",
    "TrafficConfig",
    "EndpointMetrics",
    "DeploymentStatus",
    "VariantStatus",
]
