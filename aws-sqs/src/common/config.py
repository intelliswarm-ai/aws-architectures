"""Configuration settings for the banking platform."""

import os
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Configuration
    aws_region: str = "eu-central-2"

    # SQS Configuration
    transaction_queue_url: str = ""
    dlq_queue_url: str = ""
    visibility_timeout: int = 60
    max_receive_count: int = 3
    wait_time_seconds: int = 20
    max_number_of_messages: int = 10

    # DynamoDB Configuration
    transactions_table_name: str = "banking-transactions"
    idempotency_table_name: str = "banking-idempotency"

    # Processing Configuration
    worker_threads: int = 4
    batch_size: int = 10
    processing_timeout: int = 30

    # Logging Configuration
    log_level: str = "INFO"
    service_name: str = "banking-platform"

    # Application Configuration
    environment: str = "dev"

    class Config:
        env_prefix = ""
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
