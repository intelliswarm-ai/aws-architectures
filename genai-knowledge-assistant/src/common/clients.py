"""AWS client initialization optimized for Lambda."""

from functools import lru_cache

import boto3
from botocore.config import Config

from src.common.config import get_settings

# Optimized configuration for Lambda
LAMBDA_CONFIG = Config(
    connect_timeout=5,
    read_timeout=60,
    retries={"max_attempts": 3, "mode": "adaptive"},
)

# Configuration for long-running operations (Bedrock inference)
BEDROCK_CONFIG = Config(
    connect_timeout=5,
    read_timeout=120,
    retries={"max_attempts": 3, "mode": "adaptive"},
)

# Configuration for OpenSearch operations
OPENSEARCH_CONFIG = Config(
    connect_timeout=10,
    read_timeout=60,
    retries={"max_attempts": 3, "mode": "adaptive"},
)


@lru_cache
def get_bedrock_runtime_client():
    """Get Bedrock Runtime client for model inference."""
    settings = get_settings()
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        config=BEDROCK_CONFIG,
    )


@lru_cache
def get_bedrock_agent_runtime_client():
    """Get Bedrock Agent Runtime client for agent invocations."""
    settings = get_settings()
    return boto3.client(
        "bedrock-agent-runtime",
        region_name=settings.aws_region,
        config=BEDROCK_CONFIG,
    )


@lru_cache
def get_bedrock_agent_client():
    """Get Bedrock Agent client for agent management."""
    settings = get_settings()
    return boto3.client(
        "bedrock-agent",
        region_name=settings.aws_region,
        config=LAMBDA_CONFIG,
    )


@lru_cache
def get_dynamodb_resource():
    """Get DynamoDB resource."""
    settings = get_settings()
    return boto3.resource(
        "dynamodb",
        region_name=settings.aws_region,
        config=LAMBDA_CONFIG,
    )


@lru_cache
def get_dynamodb_client():
    """Get DynamoDB client."""
    settings = get_settings()
    return boto3.client(
        "dynamodb",
        region_name=settings.aws_region,
        config=LAMBDA_CONFIG,
    )


@lru_cache
def get_s3_client():
    """Get S3 client."""
    settings = get_settings()
    return boto3.client(
        "s3",
        region_name=settings.aws_region,
        config=LAMBDA_CONFIG,
    )


@lru_cache
def get_opensearch_serverless_client():
    """Get OpenSearch Serverless client."""
    settings = get_settings()
    return boto3.client(
        "opensearchserverless",
        region_name=settings.aws_region,
        config=OPENSEARCH_CONFIG,
    )


@lru_cache
def get_sqs_client():
    """Get SQS client."""
    settings = get_settings()
    return boto3.client(
        "sqs",
        region_name=settings.aws_region,
        config=LAMBDA_CONFIG,
    )


@lru_cache
def get_eventbridge_client():
    """Get EventBridge client."""
    settings = get_settings()
    return boto3.client(
        "events",
        region_name=settings.aws_region,
        config=LAMBDA_CONFIG,
    )


@lru_cache
def get_cloudwatch_client():
    """Get CloudWatch client for custom metrics."""
    settings = get_settings()
    return boto3.client(
        "cloudwatch",
        region_name=settings.aws_region,
        config=LAMBDA_CONFIG,
    )


class AWSClients:
    """Container for all AWS clients."""

    def __init__(self) -> None:
        self._settings = get_settings()

    @property
    def bedrock_runtime(self):
        """Bedrock Runtime client."""
        return get_bedrock_runtime_client()

    @property
    def bedrock_agent_runtime(self):
        """Bedrock Agent Runtime client."""
        return get_bedrock_agent_runtime_client()

    @property
    def bedrock_agent(self):
        """Bedrock Agent client."""
        return get_bedrock_agent_client()

    @property
    def dynamodb(self):
        """DynamoDB resource."""
        return get_dynamodb_resource()

    @property
    def dynamodb_client(self):
        """DynamoDB client."""
        return get_dynamodb_client()

    @property
    def s3(self):
        """S3 client."""
        return get_s3_client()

    @property
    def opensearch_serverless(self):
        """OpenSearch Serverless client."""
        return get_opensearch_serverless_client()

    @property
    def sqs(self):
        """SQS client."""
        return get_sqs_client()

    @property
    def eventbridge(self):
        """EventBridge client."""
        return get_eventbridge_client()

    @property
    def cloudwatch(self):
        """CloudWatch client."""
        return get_cloudwatch_client()


@lru_cache
def get_clients() -> AWSClients:
    """Get cached AWS clients container."""
    return AWSClients()
