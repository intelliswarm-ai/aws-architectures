"""AWS client configuration optimized for Lambda and VPC environments."""

from functools import lru_cache
from typing import Any

import boto3
from botocore.config import Config

from src.common.config import get_settings


class AWSClients:
    """Centralized AWS client management with lazy loading and VPC awareness.

    Optimized for Lambda cold starts by:
    - Lazy loading clients only when needed
    - Reusing clients across invocations
    - Using adaptive retry mode for VPC endpoints
    - Configuring appropriate timeouts
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._clients: dict[str, Any] = {}

        # Base config optimized for Lambda/VPC
        self._base_config = Config(
            region_name=self._settings.aws_region,
            retries={
                "max_attempts": 3,
                "mode": "adaptive",
            },
            connect_timeout=5,
            read_timeout=30,
        )

        # Fast config for simple operations
        self._fast_config = Config(
            region_name=self._settings.aws_region,
            retries={
                "max_attempts": 2,
                "mode": "standard",
            },
            connect_timeout=3,
            read_timeout=10,
        )

    def _get_client(self, service: str, config: Config | None = None) -> Any:
        """Get or create a boto3 client."""
        if service not in self._clients:
            self._clients[service] = boto3.client(
                service,
                config=config or self._base_config,
            )
        return self._clients[service]

    @property
    def dynamodb(self) -> Any:
        """DynamoDB client."""
        return self._get_client("dynamodb")

    @property
    def dynamodb_resource(self) -> Any:
        """DynamoDB resource for higher-level operations."""
        if "dynamodb_resource" not in self._clients:
            self._clients["dynamodb_resource"] = boto3.resource(
                "dynamodb",
                config=self._base_config,
            )
        return self._clients["dynamodb_resource"]

    @property
    def sqs(self) -> Any:
        """SQS client."""
        return self._get_client("sqs")

    @property
    def sns(self) -> Any:
        """SNS client."""
        return self._get_client("sns")

    @property
    def s3(self) -> Any:
        """S3 client."""
        return self._get_client("s3")

    @property
    def secrets_manager(self) -> Any:
        """Secrets Manager client."""
        return self._get_client("secretsmanager")

    @property
    def ssm(self) -> Any:
        """SSM Parameter Store client."""
        return self._get_client("ssm", self._fast_config)

    @property
    def kms(self) -> Any:
        """KMS client."""
        return self._get_client("kms", self._fast_config)

    @property
    def events(self) -> Any:
        """EventBridge client."""
        return self._get_client("events")

    @property
    def cognito_idp(self) -> Any:
        """Cognito Identity Provider client."""
        return self._get_client("cognito-idp")

    @property
    def sts(self) -> Any:
        """STS client for cross-account operations."""
        return self._get_client("sts", self._fast_config)

    @property
    def cloudwatch(self) -> Any:
        """CloudWatch client for metrics."""
        return self._get_client("cloudwatch")

    @property
    def logs(self) -> Any:
        """CloudWatch Logs client."""
        return self._get_client("logs")

    def assume_role(
        self,
        role_arn: str,
        session_name: str,
        external_id: str | None = None,
        duration_seconds: int = 3600,
    ) -> dict[str, Any]:
        """Assume an IAM role and return credentials.

        Args:
            role_arn: The ARN of the role to assume
            session_name: A name for the session
            external_id: External ID for cross-account access
            duration_seconds: Duration of the session (default 1 hour)

        Returns:
            Credentials dictionary with AccessKeyId, SecretAccessKey, SessionToken
        """
        params: dict[str, Any] = {
            "RoleArn": role_arn,
            "RoleSessionName": session_name,
            "DurationSeconds": duration_seconds,
        }

        if external_id:
            params["ExternalId"] = external_id

        response = self.sts.assume_role(**params)
        return response["Credentials"]

    def get_cross_account_client(
        self,
        service: str,
        role_arn: str,
        external_id: str | None = None,
    ) -> Any:
        """Create a client using cross-account credentials.

        Args:
            service: AWS service name (e.g., 's3', 'dynamodb')
            role_arn: ARN of the role to assume
            external_id: External ID for the assume role call

        Returns:
            Boto3 client for the specified service with cross-account credentials
        """
        credentials = self.assume_role(
            role_arn=role_arn,
            session_name=f"{service}-cross-account",
            external_id=external_id,
        )

        return boto3.client(
            service,
            aws_access_key_id=credentials["AccessKeyId"],
            aws_secret_access_key=credentials["SecretAccessKey"],
            aws_session_token=credentials["SessionToken"],
            config=self._base_config,
        )


@lru_cache
def get_aws_clients() -> AWSClients:
    """Get cached AWS clients instance."""
    return AWSClients()


# Convenience functions for direct client access
def get_dynamodb_table(table_name: str) -> Any:
    """Get a DynamoDB Table resource."""
    clients = get_aws_clients()
    return clients.dynamodb_resource.Table(table_name)
