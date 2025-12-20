"""Configuration settings using Pydantic Settings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Region
    aws_region: str = "eu-central-2"

    # S3 Buckets
    raw_bucket: str = ""
    processed_bucket: str = ""
    model_bucket: str = ""

    # DynamoDB
    documents_table: str = ""
    features_table: str = ""

    # SQS
    processing_queue_url: str = ""
    dlq_url: str = ""

    # SNS
    success_topic_arn: str = ""
    failure_topic_arn: str = ""
    alert_topic_arn: str = ""

    # Step Functions
    workflow_arn: str = ""
    training_workflow_arn: str = ""

    # SageMaker
    sagemaker_endpoint_name: str = ""
    sagemaker_model_name: str = ""
    training_instance_type: str = "ml.m5.xlarge"
    endpoint_instance_type: str = "ml.m5.large"

    # Bedrock
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"
    bedrock_max_tokens: int = 4096
    bedrock_temperature: float = 0.7

    # Feature flags
    enable_pii_detection: bool = True
    enable_moderation: bool = True
    enable_summarization: bool = True
    enable_qa_generation: bool = True

    # Logging
    log_level: str = "INFO"
    powertools_service_name: str = "ml-platform"

    # Timeouts (seconds)
    textract_timeout: int = 300
    transcribe_timeout: int = 600
    inference_timeout: int = 60
    generation_timeout: int = 120


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
