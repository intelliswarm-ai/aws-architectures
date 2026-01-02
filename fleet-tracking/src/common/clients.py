"""AWS client initialization and management."""

from functools import lru_cache

import boto3
from botocore.config import Config

from .config import get_settings


def _get_boto_config() -> Config:
    """Get boto3 client configuration."""
    settings = get_settings()
    return Config(
        region_name=settings.aws_region,
        retries={
            "max_attempts": 3,
            "mode": "adaptive",
        },
    )


@lru_cache
def get_kinesis_client():
    """Get cached Kinesis client."""
    return boto3.client("kinesis", config=_get_boto_config())


@lru_cache
def get_dynamodb_client():
    """Get cached DynamoDB client."""
    return boto3.client("dynamodb", config=_get_boto_config())


@lru_cache
def get_dynamodb_resource():
    """Get cached DynamoDB resource."""
    settings = get_settings()
    return boto3.resource("dynamodb", region_name=settings.aws_region)


@lru_cache
def get_s3_client():
    """Get cached S3 client."""
    return boto3.client("s3", config=_get_boto_config())


@lru_cache
def get_sns_client():
    """Get cached SNS client."""
    return boto3.client("sns", config=_get_boto_config())


@lru_cache
def get_cloudwatch_client():
    """Get cached CloudWatch client."""
    return boto3.client("cloudwatch", config=_get_boto_config())
