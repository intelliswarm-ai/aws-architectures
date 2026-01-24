"""Configuration settings for ML Canary Deployment system."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Configuration
    aws_region: str = "eu-central-1"

    # SageMaker Configuration
    sagemaker_endpoint_name: str = ""
    sagemaker_model_bucket: str = ""
    sagemaker_execution_role_arn: str = ""
    default_instance_type: str = "ml.m5.xlarge"
    default_instance_count: int = 1

    # DynamoDB Configuration
    deployments_table: str = ""
    metrics_table: str = ""
    events_table: str = ""

    # S3 Configuration
    model_artifacts_bucket: str = ""
    inference_logs_bucket: str = ""

    # SNS Configuration
    alerts_topic_arn: str = ""
    deployment_events_topic_arn: str = ""

    # Monitoring Thresholds
    latency_threshold_ms: float = 100.0
    error_rate_threshold: float = 0.01
    cpu_utilization_threshold: float = 80.0
    memory_utilization_threshold: float = 80.0

    # Canary Deployment Settings
    default_canary_weight: float = 0.1
    default_step_size: float = 0.1
    default_bake_time_minutes: int = 10
    max_deployment_duration_hours: int = 24

    # Auto-scaling Settings
    min_instance_count: int = 1
    max_instance_count: int = 10
    target_invocations_per_instance: int = 1000
    scale_in_cooldown_seconds: int = 300
    scale_out_cooldown_seconds: int = 60

    # Feature Flags
    enable_auto_rollback: bool = True
    enable_auto_scaling: bool = True
    enable_detailed_metrics: bool = True
    enable_inference_logging: bool = True

    # Logging Configuration
    log_level: str = "INFO"
    enable_xray_tracing: bool = True


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
