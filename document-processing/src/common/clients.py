"""AWS client configuration optimized for Lambda."""

from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config

from .config import get_settings

# Optimized config for Lambda
LAMBDA_CONFIG = Config(
    connect_timeout=5,
    read_timeout=60,
    retries={"max_attempts": 3, "mode": "adaptive"},
)

# Config for long-running operations (Textract async, Transcribe)
ASYNC_CONFIG = Config(
    connect_timeout=5,
    read_timeout=300,
    retries={"max_attempts": 3, "mode": "adaptive"},
)

# Config for Bedrock (may need longer timeouts)
BEDROCK_CONFIG = Config(
    connect_timeout=10,
    read_timeout=120,
    retries={"max_attempts": 3, "mode": "adaptive"},
)


class AWSClients:
    """Lazy-loaded AWS clients optimized for Lambda cold starts."""

    def __init__(self, region: str | None = None):
        self._region = region or get_settings().aws_region
        self._clients: dict[str, Any] = {}

    def _get_client(self, service: str, config: Config = LAMBDA_CONFIG) -> Any:
        """Get or create a client for the specified service."""
        if service not in self._clients:
            self._clients[service] = boto3.client(
                service,
                region_name=self._region,
                config=config,
            )
        return self._clients[service]

    @property
    def s3(self) -> Any:
        """S3 client."""
        return self._get_client("s3")

    @property
    def dynamodb(self) -> Any:
        """DynamoDB client."""
        return self._get_client("dynamodb")

    @property
    def sqs(self) -> Any:
        """SQS client."""
        return self._get_client("sqs")

    @property
    def sns(self) -> Any:
        """SNS client."""
        return self._get_client("sns")

    @property
    def sfn(self) -> Any:
        """Step Functions client."""
        return self._get_client("stepfunctions")

    @property
    def textract(self) -> Any:
        """Textract client."""
        return self._get_client("textract", ASYNC_CONFIG)

    @property
    def comprehend(self) -> Any:
        """Comprehend client."""
        return self._get_client("comprehend")

    @property
    def rekognition(self) -> Any:
        """Rekognition client."""
        return self._get_client("rekognition")

    @property
    def transcribe(self) -> Any:
        """Transcribe client."""
        return self._get_client("transcribe", ASYNC_CONFIG)

    @property
    def sagemaker_runtime(self) -> Any:
        """SageMaker Runtime client for inference."""
        return self._get_client("sagemaker-runtime")

    @property
    def sagemaker(self) -> Any:
        """SageMaker client for training/management."""
        return self._get_client("sagemaker")

    @property
    def bedrock_runtime(self) -> Any:
        """Bedrock Runtime client for inference."""
        return self._get_client("bedrock-runtime", BEDROCK_CONFIG)

    @property
    def bedrock(self) -> Any:
        """Bedrock client for model management."""
        return self._get_client("bedrock", BEDROCK_CONFIG)

    @property
    def ses(self) -> Any:
        """SES client for email."""
        return self._get_client("ses")


@lru_cache
def get_clients(region: str | None = None) -> AWSClients:
    """Get cached AWS clients instance."""
    return AWSClients(region)


@lru_cache
def get_bedrock_client(region: str | None = None) -> Any:
    """Get Bedrock Runtime client."""
    return get_clients(region).bedrock_runtime


@lru_cache
def get_dynamodb_resource(region: str | None = None) -> Any:
    """Get DynamoDB resource for higher-level operations."""
    settings = get_settings()
    return boto3.resource(
        "dynamodb",
        region_name=region or settings.aws_region,
        config=LAMBDA_CONFIG,
    )
