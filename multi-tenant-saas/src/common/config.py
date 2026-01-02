"""Configuration settings with Secrets Manager integration."""

import json
from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and Secrets Manager."""

    model_config = SettingsConfigDict(
        env_prefix="",
        case_sensitive=False,
        extra="ignore",
    )

    # AWS Configuration
    aws_region: str = Field("eu-central-2", alias="AWS_REGION")
    environment: str = Field("dev", alias="ENVIRONMENT")
    project_name: str = Field("enterprise-api", alias="PROJECT_NAME")

    # VPC Configuration (for VPC-deployed Lambdas)
    vpc_enabled: bool = Field(False, alias="VPC_ENABLED")

    # Cognito Configuration
    cognito_user_pool_id: str = Field("", alias="COGNITO_USER_POOL_ID")
    cognito_client_id: str = Field("", alias="COGNITO_CLIENT_ID")
    cognito_region: str = Field("", alias="COGNITO_REGION")

    # DynamoDB Tables
    tenant_table: str = Field("", alias="TENANT_TABLE")
    audit_table: str = Field("", alias="AUDIT_TABLE")

    # SQS Queues
    processing_queue_url: str = Field("", alias="PROCESSING_QUEUE_URL")
    dlq_url: str = Field("", alias="DLQ_URL")

    # SNS Topics
    notification_topic_arn: str = Field("", alias="NOTIFICATION_TOPIC_ARN")
    alert_topic_arn: str = Field("", alias="ALERT_TOPIC_ARN")

    # EventBridge
    event_bus_name: str = Field("default", alias="EVENT_BUS_NAME")

    # KMS
    kms_key_id: str = Field("", alias="KMS_KEY_ID")

    # Secrets Manager
    db_secret_arn: str = Field("", alias="DB_SECRET_ARN")
    api_secret_arn: str = Field("", alias="API_SECRET_ARN")

    # Cache Configuration
    cache_endpoint: str = Field("", alias="CACHE_ENDPOINT")
    cache_port: int = Field(6379, alias="CACHE_PORT")

    # Database Configuration (from Secrets Manager)
    db_host: str = Field("", alias="DB_HOST")
    db_port: int = Field(5432, alias="DB_PORT")
    db_name: str = Field("", alias="DB_NAME")

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    powertools_service_name: str = Field("enterprise-api", alias="POWERTOOLS_SERVICE_NAME")

    # Feature Flags
    enable_audit_logging: bool = Field(True, alias="ENABLE_AUDIT_LOGGING")
    enable_request_validation: bool = Field(True, alias="ENABLE_REQUEST_VALIDATION")
    enable_rate_limiting: bool = Field(True, alias="ENABLE_RATE_LIMITING")

    # Rate Limiting
    default_rate_limit: int = Field(100, alias="DEFAULT_RATE_LIMIT")
    rate_limit_window_seconds: int = Field(60, alias="RATE_LIMIT_WINDOW_SECONDS")

    # Timeouts
    api_timeout: int = Field(30, alias="API_TIMEOUT")
    db_timeout: int = Field(10, alias="DB_TIMEOUT")
    cache_timeout: int = Field(5, alias="CACHE_TIMEOUT")

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "prod"

    @property
    def cognito_issuer(self) -> str:
        """Get Cognito issuer URL for JWT validation."""
        region = self.cognito_region or self.aws_region
        return f"https://cognito-idp.{region}.amazonaws.com/{self.cognito_user_pool_id}"

    @property
    def cognito_jwks_url(self) -> str:
        """Get Cognito JWKS URL for JWT validation."""
        return f"{self.cognito_issuer}/.well-known/jwks.json"


class SecretsManager:
    """Secrets Manager helper for loading secrets."""

    def __init__(self, region: str | None = None) -> None:
        config = Config(
            region_name=region or "eu-central-2",
            retries={"max_attempts": 3, "mode": "adaptive"},
        )
        self._client = boto3.client("secretsmanager", config=config)
        self._cache: dict[str, dict[str, Any]] = {}

    def get_secret(self, secret_id: str) -> dict[str, Any]:
        """Get secret value from Secrets Manager with caching."""
        if secret_id in self._cache:
            return self._cache[secret_id]

        response = self._client.get_secret_value(SecretId=secret_id)
        secret_string = response.get("SecretString", "{}")
        secret_value = json.loads(secret_string)

        self._cache[secret_id] = secret_value
        return secret_value

    def get_database_credentials(self, secret_id: str) -> dict[str, str]:
        """Get database credentials from secret."""
        secret = self.get_secret(secret_id)
        return {
            "host": secret.get("host", ""),
            "port": str(secret.get("port", 5432)),
            "database": secret.get("dbname", ""),
            "username": secret.get("username", ""),
            "password": secret.get("password", ""),
        }

    def clear_cache(self) -> None:
        """Clear the secrets cache (useful for rotation)."""
        self._cache.clear()


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


@lru_cache
def get_secrets_manager() -> SecretsManager:
    """Get cached secrets manager instance."""
    settings = get_settings()
    return SecretsManager(region=settings.aws_region)
