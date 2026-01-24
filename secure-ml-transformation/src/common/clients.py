"""AWS service clients with singleton pattern."""

from functools import lru_cache
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config

from src.common.config import get_settings

if TYPE_CHECKING:
    from mypy_boto3_glue import GlueClient
    from mypy_boto3_kms import KMSClient
    from mypy_boto3_logs import CloudWatchLogsClient
    from mypy_boto3_s3 import S3Client


def _get_boto_config() -> Config:
    """Get boto3 client configuration with retries."""
    return Config(
        retries={"max_attempts": 3, "mode": "adaptive"},
        connect_timeout=5,
        read_timeout=30,
    )


@lru_cache
def get_s3_client() -> "S3Client":
    """Get cached S3 client."""
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        config=_get_boto_config(),
    )


@lru_cache
def get_glue_client() -> "GlueClient":
    """Get cached Glue client."""
    settings = get_settings()
    return boto3.client(
        "glue",
        region_name=settings.aws_region,
        config=_get_boto_config(),
    )


@lru_cache
def get_kms_client() -> "KMSClient":
    """Get cached KMS client."""
    settings = get_settings()
    return boto3.client(
        "kms",
        region_name=settings.aws_region,
        config=_get_boto_config(),
    )


@lru_cache
def get_cloudwatch_logs_client() -> "CloudWatchLogsClient":
    """Get cached CloudWatch Logs client."""
    settings = get_settings()
    return boto3.client(
        "logs",
        region_name=settings.aws_region,
        config=_get_boto_config(),
    )


def clear_client_cache() -> None:
    """Clear all cached clients. Useful for testing."""
    get_s3_client.cache_clear()
    get_glue_client.cache_clear()
    get_kms_client.cache_clear()
    get_cloudwatch_logs_client.cache_clear()
