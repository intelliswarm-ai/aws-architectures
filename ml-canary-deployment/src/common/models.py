"""Pydantic models for ML Canary Deployment system."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator


class DeploymentStatus(str, Enum):
    """Status of a model deployment."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    ROLLING_BACK = "ROLLING_BACK"
    ROLLED_BACK = "ROLLED_BACK"


class VariantStatus(str, Enum):
    """Status of an endpoint variant."""

    CREATING = "Creating"
    UPDATING = "Updating"
    IN_SERVICE = "InService"
    DELETING = "Deleting"
    FAILED = "Failed"


class ContentType(str, Enum):
    """Supported content types for inference."""

    JSON = "application/json"
    CSV = "text/csv"
    NUMPY = "application/x-npy"


class ModelVariant(BaseModel):
    """Configuration for a SageMaker production variant."""

    variant_name: str = Field(..., description="Unique name for the variant")
    model_name: str = Field(..., description="Name of the SageMaker model")
    instance_type: str = Field(
        default="ml.m5.xlarge", description="EC2 instance type for hosting"
    )
    initial_instance_count: int = Field(
        default=1, ge=1, description="Initial number of instances"
    )
    initial_weight: float = Field(
        default=1.0, ge=0.0, le=1.0, description="Initial traffic weight (0-1)"
    )
    accelerator_type: str | None = Field(
        default=None, description="Optional elastic inference accelerator"
    )
    model_data_download_timeout: int = Field(
        default=3600, ge=60, description="Model download timeout in seconds"
    )
    container_startup_health_check_timeout: int = Field(
        default=600, ge=60, description="Container startup timeout in seconds"
    )

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class TrafficConfig(BaseModel):
    """Traffic splitting configuration for canary deployment."""

    variant_weights: dict[str, float] = Field(
        ..., description="Mapping of variant names to traffic weights"
    )
    canary_size: float = Field(
        default=0.1, ge=0.01, le=0.5, description="Initial canary traffic percentage"
    )
    step_size: float = Field(
        default=0.1, ge=0.05, le=0.5, description="Traffic shift increment"
    )
    bake_time_minutes: int = Field(
        default=10, ge=1, le=1440, description="Wait time between traffic shifts"
    )
    max_rollback_weight: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Weight threshold for auto-rollback"
    )

    @field_validator("variant_weights")
    @classmethod
    def validate_weights_sum(cls, v: dict[str, float]) -> dict[str, float]:
        """Validate that weights sum to approximately 1.0."""
        total = sum(v.values())
        if not (0.99 <= total <= 1.01):
            raise ValueError(f"Variant weights must sum to 1.0, got {total}")
        return v


class DeploymentConfig(BaseModel):
    """Configuration for a canary deployment."""

    deployment_id: str = Field(..., description="Unique deployment identifier")
    endpoint_name: str = Field(..., description="SageMaker endpoint name")
    current_variant: ModelVariant = Field(..., description="Current production variant")
    canary_variant: ModelVariant = Field(..., description="New canary variant to deploy")
    traffic_config: TrafficConfig = Field(..., description="Traffic splitting configuration")
    status: DeploymentStatus = Field(
        default=DeploymentStatus.PENDING, description="Current deployment status"
    )
    auto_rollback_enabled: bool = Field(
        default=True, description="Enable automatic rollback on errors"
    )
    latency_threshold_ms: float = Field(
        default=100.0, ge=1.0, description="Maximum acceptable P99 latency in ms"
    )
    error_rate_threshold: float = Field(
        default=0.01, ge=0.0, le=1.0, description="Maximum acceptable error rate"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class InferenceRequest(BaseModel):
    """Request model for real-time inference."""

    request_id: str = Field(..., description="Unique request identifier")
    user_id: str = Field(..., description="User identifier for recommendations")
    features: dict[str, Any] = Field(..., description="Feature dictionary for inference")
    content_type: ContentType = Field(
        default=ContentType.JSON, description="Request content type"
    )
    target_variant: str | None = Field(
        default=None, description="Optional target variant override"
    )
    request_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class InferenceResponse(BaseModel):
    """Response model for real-time inference."""

    request_id: str = Field(..., description="Original request identifier")
    predictions: list[dict[str, Any]] = Field(..., description="Model predictions")
    variant_name: str = Field(..., description="Variant that served the request")
    model_latency_ms: float = Field(..., description="Model inference latency in ms")
    total_latency_ms: float = Field(..., description="Total request latency in ms")
    response_timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic configuration."""

        use_enum_values = True


class EndpointMetrics(BaseModel):
    """CloudWatch metrics for an endpoint variant."""

    variant_name: str = Field(..., description="Variant name")
    endpoint_name: str = Field(..., description="Endpoint name")
    invocation_count: int = Field(default=0, description="Total invocations")
    invocation_4xx_errors: int = Field(default=0, description="4xx error count")
    invocation_5xx_errors: int = Field(default=0, description="5xx error count")
    model_latency_p50_ms: float = Field(default=0.0, description="P50 model latency")
    model_latency_p90_ms: float = Field(default=0.0, description="P90 model latency")
    model_latency_p99_ms: float = Field(default=0.0, description="P99 model latency")
    overhead_latency_ms: float = Field(default=0.0, description="Overhead latency")
    cpu_utilization: float = Field(default=0.0, description="CPU utilization percentage")
    memory_utilization: float = Field(default=0.0, description="Memory utilization percentage")
    gpu_utilization: float | None = Field(default=None, description="GPU utilization if applicable")
    disk_utilization: float = Field(default=0.0, description="Disk utilization percentage")
    error_rate: float = Field(default=0.0, description="Calculated error rate")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    @property
    def is_healthy(self) -> bool:
        """Check if the variant is healthy based on metrics."""
        return self.error_rate < 0.01 and self.model_latency_p99_ms < 100.0


class TrafficShiftEvent(BaseModel):
    """Event record for a traffic shift operation."""

    deployment_id: str = Field(..., description="Deployment identifier")
    event_id: str = Field(..., description="Unique event identifier")
    from_weights: dict[str, float] = Field(..., description="Previous traffic weights")
    to_weights: dict[str, float] = Field(..., description="New traffic weights")
    reason: str = Field(..., description="Reason for traffic shift")
    triggered_by: str = Field(..., description="User or system that triggered shift")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RollbackEvent(BaseModel):
    """Event record for a rollback operation."""

    deployment_id: str = Field(..., description="Deployment identifier")
    event_id: str = Field(..., description="Unique event identifier")
    reason: str = Field(..., description="Reason for rollback")
    metrics_snapshot: EndpointMetrics = Field(..., description="Metrics at rollback time")
    triggered_by: str = Field(..., description="User or system that triggered rollback")
    automatic: bool = Field(default=False, description="Was this an automatic rollback")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AutoScalingConfig(BaseModel):
    """Auto-scaling configuration for endpoint variants."""

    min_capacity: int = Field(default=1, ge=1, description="Minimum instance count")
    max_capacity: int = Field(default=10, ge=1, description="Maximum instance count")
    target_invocations_per_instance: int = Field(
        default=1000, ge=1, description="Target invocations per instance for scaling"
    )
    scale_in_cooldown: int = Field(default=300, ge=0, description="Scale in cooldown seconds")
    scale_out_cooldown: int = Field(default=60, ge=0, description="Scale out cooldown seconds")


class RecommendationItem(BaseModel):
    """A single content recommendation."""

    content_id: str = Field(..., description="Content identifier")
    title: str = Field(..., description="Content title")
    score: float = Field(..., ge=0.0, le=1.0, description="Recommendation score")
    content_type: str = Field(..., description="Type of content (movie, series, etc)")
    genre: list[str] = Field(default_factory=list, description="Content genres")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class UserContext(BaseModel):
    """User context for personalized recommendations."""

    user_id: str = Field(..., description="User identifier")
    watch_history: list[str] = Field(default_factory=list, description="Recent watch history")
    preferences: dict[str, Any] = Field(default_factory=dict, description="User preferences")
    device_type: str = Field(default="unknown", description="User's device type")
    session_id: str | None = Field(default=None, description="Current session identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
