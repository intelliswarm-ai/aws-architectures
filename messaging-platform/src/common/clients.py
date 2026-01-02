"""AWS client initialization for the SMS Marketing System."""

from functools import lru_cache

import boto3
from botocore.config import Config

from .config import settings

# Boto3 configuration with retry logic
boto_config = Config(
    region_name=settings.aws_region,
    retries={
        "max_attempts": 3,
        "mode": "adaptive",
    },
)


@lru_cache
def get_kinesis_client():
    """Get cached Kinesis client."""
    return boto3.client("kinesis", config=boto_config)


@lru_cache
def get_dynamodb_client():
    """Get cached DynamoDB client."""
    return boto3.client("dynamodb", config=boto_config)


@lru_cache
def get_dynamodb_resource():
    """Get cached DynamoDB resource."""
    return boto3.resource("dynamodb", config=boto_config)


@lru_cache
def get_s3_client():
    """Get cached S3 client."""
    return boto3.client("s3", config=boto_config)


@lru_cache
def get_sns_client():
    """Get cached SNS client."""
    return boto3.client("sns", config=boto_config)


@lru_cache
def get_pinpoint_client():
    """Get cached Pinpoint client."""
    return boto3.client("pinpoint", config=boto_config)


@lru_cache
def get_cloudwatch_client():
    """Get cached CloudWatch client."""
    return boto3.client("cloudwatch", config=boto_config)
