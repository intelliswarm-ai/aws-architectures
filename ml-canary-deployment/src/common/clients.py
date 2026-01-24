"""AWS client management for ML Canary Deployment system."""

from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config

from src.common.config import get_settings

# Optimized config for Lambda with adaptive retries
LAMBDA_CONFIG = Config(
    connect_timeout=5,
    read_timeout=60,
    retries={
        "max_attempts": 3,
        "mode": "adaptive",
    },
)

# Low-latency config for real-time inference
INFERENCE_CONFIG = Config(
    connect_timeout=2,
    read_timeout=30,
    retries={
        "max_attempts": 2,
        "mode": "standard",
    },
)


class AWSClients:
    """Lazy-loaded AWS client manager optimized for Lambda cold starts."""

    def __init__(self, region: str | None = None):
        """Initialize AWS clients manager.

        Args:
            region: AWS region override. Uses settings if not provided.
        """
        self._settings = get_settings()
        self._region = region or self._settings.aws_region
        self._clients: dict[str, Any] = {}

    def _get_client(
        self, service: str, config: Config = LAMBDA_CONFIG
    ) -> Any:
        """Get or create a boto3 client for the specified service.

        Args:
            service: AWS service name.
            config: Botocore configuration.

        Returns:
            Boto3 client for the service.
        """
        cache_key = f"{service}_{id(config)}"
        if cache_key not in self._clients:
            self._clients[cache_key] = boto3.client(
                service,
                region_name=self._region,
                config=config,
            )
        return self._clients[cache_key]

    def _get_resource(self, service: str) -> Any:
        """Get or create a boto3 resource for the specified service.

        Args:
            service: AWS service name.

        Returns:
            Boto3 resource for the service.
        """
        cache_key = f"{service}_resource"
        if cache_key not in self._clients:
            self._clients[cache_key] = boto3.resource(
                service,
                region_name=self._region,
            )
        return self._clients[cache_key]

    @property
    def sagemaker(self) -> Any:
        """Get SageMaker client for endpoint and model management."""
        return self._get_client("sagemaker")

    @property
    def sagemaker_runtime(self) -> Any:
        """Get SageMaker Runtime client for real-time inference."""
        return self._get_client("sagemaker-runtime", INFERENCE_CONFIG)

    @property
    def dynamodb(self) -> Any:
        """Get DynamoDB client."""
        return self._get_client("dynamodb")

    @property
    def dynamodb_resource(self) -> Any:
        """Get DynamoDB resource for higher-level operations."""
        return self._get_resource("dynamodb")

    @property
    def s3(self) -> Any:
        """Get S3 client."""
        return self._get_client("s3")

    @property
    def cloudwatch(self) -> Any:
        """Get CloudWatch client for metrics."""
        return self._get_client("cloudwatch")

    @property
    def cloudwatch_logs(self) -> Any:
        """Get CloudWatch Logs client."""
        return self._get_client("logs")

    @property
    def sns(self) -> Any:
        """Get SNS client for notifications."""
        return self._get_client("sns")

    @property
    def application_autoscaling(self) -> Any:
        """Get Application Auto Scaling client."""
        return self._get_client("application-autoscaling")

    @property
    def events(self) -> Any:
        """Get EventBridge client."""
        return self._get_client("events")

    @property
    def sts(self) -> Any:
        """Get STS client for account info."""
        return self._get_client("sts")


@lru_cache
def get_clients(region: str | None = None) -> AWSClients:
    """Get cached AWS clients instance.

    Args:
        region: Optional AWS region override.

    Returns:
        AWSClients instance.
    """
    return AWSClients(region=region)
