"""Configuration settings for the SMS Marketing System."""

from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Configuration
    aws_region: str = "eu-central-2"

    # Kinesis Configuration
    stream_name: str = "sms-events-stream"

    # DynamoDB Configuration
    responses_table: str = "sms-responses"
    subscribers_table: str = "subscribers"

    # S3 Configuration
    archive_bucket: str = "sms-archive"

    # SNS Configuration
    notifications_topic: str = ""

    # Pinpoint Configuration
    pinpoint_app_id: str = ""

    # Logging
    log_level: str = "INFO"

    # Processing Configuration
    batch_size: int = 100
    ttl_days: int = 365  # 1 year retention for responses

    class Config:
        env_prefix = ""
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
