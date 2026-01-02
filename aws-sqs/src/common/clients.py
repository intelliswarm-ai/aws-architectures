"""AWS service clients."""

from functools import lru_cache

import boto3
from botocore.config import Config

from .config import settings


def get_boto_config() -> Config:
    """Get optimized boto3 configuration."""
    return Config(
        region_name=settings.aws_region,
        retries={
            "max_attempts": 3,
            "mode": "adaptive",
        },
        connect_timeout=5,
        read_timeout=30,
    )


@lru_cache
def get_sqs_client():
    """Get cached SQS client."""
    return boto3.client("sqs", config=get_boto_config())


@lru_cache
def get_dynamodb_client():
    """Get cached DynamoDB client."""
    return boto3.client("dynamodb", config=get_boto_config())


@lru_cache
def get_cloudwatch_client():
    """Get cached CloudWatch client."""
    return boto3.client("cloudwatch", config=get_boto_config())


@lru_cache
def get_autoscaling_client():
    """Get cached Auto Scaling client."""
    return boto3.client("autoscaling", config=get_boto_config())


@lru_cache
def get_ec2_client():
    """Get cached EC2 client."""
    return boto3.client("ec2", config=get_boto_config())
