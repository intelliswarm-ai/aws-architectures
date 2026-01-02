"""Configuration settings for the GPS tracking system."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Configuration
    aws_region: str = Field(default="eu-central-2", alias="AWS_REGION")

    # Kinesis Configuration
    stream_name: str = Field(
        default="gps-coordinates-stream",
        alias="STREAM_NAME",
    )
    stream_arn: str = Field(default="", alias="STREAM_ARN")

    # DynamoDB Configuration
    positions_table: str = Field(
        default="truck-positions",
        alias="DYNAMODB_TABLE",
    )
    geofences_table: str = Field(
        default="geofences",
        alias="GEOFENCES_TABLE",
    )

    # S3 Configuration
    archive_bucket: str = Field(default="", alias="S3_BUCKET")

    # SNS Configuration
    alerts_topic_arn: str = Field(default="", alias="SNS_TOPIC_ARN")

    # Producer Configuration
    num_trucks: int = Field(default=50, alias="NUM_TRUCKS")
    batch_size: int = Field(default=100, alias="BATCH_SIZE")

    # Consumer Configuration
    consumer_batch_size: int = Field(default=100, alias="CONSUMER_BATCH_SIZE")
    max_batching_window_seconds: int = Field(
        default=5,
        alias="MAX_BATCHING_WINDOW_SECONDS",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        alias="LOG_LEVEL",
    )

    # Environment
    environment: Literal["dev", "staging", "prod"] = Field(
        default="dev",
        alias="ENVIRONMENT",
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
