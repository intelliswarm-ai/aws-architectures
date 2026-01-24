"""Service for managing canary deployments."""

from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import AWSClients
from src.common.config import Settings
from src.common.exceptions import (
    DeploymentError,
    EndpointNotFoundError,
    NonRetryableError,
    ValidationError,
)
from src.common.models import (
    DeploymentConfig,
    DeploymentStatus,
    RollbackEvent,
    TrafficShiftEvent,
)
from src.common.utils import json_serialize

logger = Logger()


class DeploymentService:
    """Service for managing SageMaker canary deployments."""

    def __init__(self, clients: AWSClients, settings: Settings):
        """Initialize deployment service.

        Args:
            clients: AWS clients instance.
            settings: Application settings.
        """
        self.clients = clients
        self.settings = settings
        self._deployments_table = settings.deployments_table
        self._events_table = settings.events_table

    def create_deployment(self, config: DeploymentConfig) -> dict[str, Any]:
        """Create a new canary deployment.

        Adds the canary variant to the existing endpoint with initial traffic weight.

        Args:
            config: Deployment configuration.

        Returns:
            Deployment result with status.

        Raises:
            DeploymentError: On deployment creation failure.
        """
        logger.info(
            "Creating canary deployment",
            deployment_id=config.deployment_id,
            endpoint_name=config.endpoint_name,
        )

        try:
            # Verify endpoint exists
            endpoint_info = self._describe_endpoint(config.endpoint_name)
            if endpoint_info["EndpointStatus"] != "InService":
                raise DeploymentError(
                    f"Endpoint is not InService: {endpoint_info['EndpointStatus']}",
                    deployment_id=config.deployment_id,
                    endpoint_name=config.endpoint_name,
                )

            # Get current endpoint configuration
            endpoint_config_name = endpoint_info["EndpointConfigName"]

            # Create new endpoint configuration with canary variant
            new_config_name = f"{config.endpoint_name}-{config.deployment_id}"
            self._create_endpoint_config_with_canary(
                new_config_name=new_config_name,
                current_config_name=endpoint_config_name,
                canary_variant=config.canary_variant,
                traffic_config=config.traffic_config,
            )

            # Update endpoint to use new configuration
            self.clients.sagemaker.update_endpoint(
                EndpointName=config.endpoint_name,
                EndpointConfigName=new_config_name,
                RetainDeploymentConfig=True,
            )

            # Store deployment record
            self._store_deployment(config)

            logger.info(
                "Deployment created successfully",
                deployment_id=config.deployment_id,
                new_config=new_config_name,
            )

            return {
                "deployment_id": config.deployment_id,
                "status": DeploymentStatus.IN_PROGRESS.value,
                "endpoint_config": new_config_name,
            }

        except ClientError as e:
            error_message = e.response.get("Error", {}).get("Message", str(e))
            raise DeploymentError(
                f"Failed to create deployment: {error_message}",
                deployment_id=config.deployment_id,
                endpoint_name=config.endpoint_name,
            )

    def _create_endpoint_config_with_canary(
        self,
        new_config_name: str,
        current_config_name: str,
        canary_variant: Any,
        traffic_config: Any,
    ) -> None:
        """Create endpoint config with canary variant added.

        Args:
            new_config_name: Name for new configuration.
            current_config_name: Current configuration name.
            canary_variant: Canary variant configuration.
            traffic_config: Traffic splitting configuration.
        """
        # Get current configuration
        current_config = self.clients.sagemaker.describe_endpoint_config(
            EndpointConfigName=current_config_name
        )

        # Build production variants list with updated weights
        production_variants = []

        # Add existing variants with updated weights
        for variant in current_config.get("ProductionVariants", []):
            variant_name = variant["VariantName"]
            weight = traffic_config.variant_weights.get(
                variant_name, variant.get("InitialVariantWeight", 1.0)
            )
            production_variants.append({
                "VariantName": variant_name,
                "ModelName": variant["ModelName"],
                "InstanceType": variant["InstanceType"],
                "InitialInstanceCount": variant["InitialInstanceCount"],
                "InitialVariantWeight": weight,
            })

        # Add canary variant
        production_variants.append({
            "VariantName": canary_variant.variant_name,
            "ModelName": canary_variant.model_name,
            "InstanceType": canary_variant.instance_type,
            "InitialInstanceCount": canary_variant.initial_instance_count,
            "InitialVariantWeight": canary_variant.initial_weight,
            "ModelDataDownloadTimeoutInSeconds": canary_variant.model_data_download_timeout,
            "ContainerStartupHealthCheckTimeoutInSeconds": (
                canary_variant.container_startup_health_check_timeout
            ),
        })

        # Create new configuration
        self.clients.sagemaker.create_endpoint_config(
            EndpointConfigName=new_config_name,
            ProductionVariants=production_variants,
        )

    def get_deployment(self, deployment_id: str) -> dict[str, Any]:
        """Get deployment details by ID.

        Args:
            deployment_id: Deployment identifier.

        Returns:
            Deployment details.

        Raises:
            ValidationError: If deployment not found.
        """
        try:
            table = self.clients.dynamodb_resource.Table(self._deployments_table)
            response = table.get_item(Key={"deployment_id": deployment_id})

            if "Item" not in response:
                raise ValidationError(f"Deployment not found: {deployment_id}")

            return response["Item"]

        except ClientError as e:
            raise DeploymentError(
                f"Failed to get deployment: {e}",
                deployment_id=deployment_id,
            )

    def get_deployment_status(self, deployment_id: str) -> dict[str, Any]:
        """Get deployment status with endpoint info.

        Args:
            deployment_id: Deployment identifier.

        Returns:
            Deployment status details.
        """
        deployment = self.get_deployment(deployment_id)
        endpoint_name = deployment["endpoint_name"]

        # Get endpoint status
        endpoint_info = self._describe_endpoint(endpoint_name)

        # Get current variant weights
        variants = {}
        for variant in endpoint_info.get("ProductionVariants", []):
            variants[variant["VariantName"]] = {
                "weight": variant.get("CurrentWeight", 0.0),
                "instance_count": variant.get("CurrentInstanceCount", 0),
                "desired_instance_count": variant.get("DesiredInstanceCount", 0),
            }

        return {
            "deployment_id": deployment_id,
            "endpoint_name": endpoint_name,
            "endpoint_status": endpoint_info["EndpointStatus"],
            "deployment_status": deployment.get("status", "UNKNOWN"),
            "variants": variants,
            "created_at": deployment.get("created_at"),
            "updated_at": deployment.get("updated_at"),
        }

    def update_deployment_status(
        self,
        deployment_id: str,
        status: DeploymentStatus,
    ) -> None:
        """Update deployment status.

        Args:
            deployment_id: Deployment identifier.
            status: New deployment status.
        """
        table = self.clients.dynamodb_resource.Table(self._deployments_table)
        table.update_item(
            Key={"deployment_id": deployment_id},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": status.value,
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

    def update_variant(
        self,
        deployment_id: str,
        variant_name: str,
        instance_count: int | None = None,
        instance_type: str | None = None,
    ) -> dict[str, Any]:
        """Update variant instance count or type.

        Args:
            deployment_id: Deployment identifier.
            variant_name: Variant to update.
            instance_count: New instance count.
            instance_type: New instance type.

        Returns:
            Update status.
        """
        deployment = self.get_deployment(deployment_id)
        endpoint_name = deployment["endpoint_name"]

        update_params = {
            "EndpointName": endpoint_name,
            "DesiredWeightsAndCapacities": [{
                "VariantName": variant_name,
            }],
        }

        if instance_count is not None:
            update_params["DesiredWeightsAndCapacities"][0][
                "DesiredInstanceCount"
            ] = instance_count

        self.clients.sagemaker.update_endpoint_weights_and_capacities(
            **update_params
        )

        return {
            "status": "updating",
            "variant_name": variant_name,
        }

    def complete_deployment(self, deployment_id: str) -> dict[str, Any]:
        """Complete deployment by promoting canary to production.

        Args:
            deployment_id: Deployment identifier.

        Returns:
            Completion status.
        """
        deployment = self.get_deployment(deployment_id)
        endpoint_name = deployment["endpoint_name"]
        canary_variant = deployment["canary_variant"]["variant_name"]

        logger.info(
            "Completing deployment, promoting canary to 100%",
            deployment_id=deployment_id,
            canary_variant=canary_variant,
        )

        # Set canary to 100% weight
        self.clients.sagemaker.update_endpoint_weights_and_capacities(
            EndpointName=endpoint_name,
            DesiredWeightsAndCapacities=[
                {"VariantName": canary_variant, "DesiredWeight": 1.0},
            ],
        )

        self.update_deployment_status(deployment_id, DeploymentStatus.COMPLETED)

        return {
            "endpoint_name": endpoint_name,
            "status": DeploymentStatus.COMPLETED.value,
        }

    def cancel_deployment(self, deployment_id: str, reason: str) -> dict[str, Any]:
        """Cancel deployment and remove canary variant.

        Args:
            deployment_id: Deployment identifier.
            reason: Cancellation reason.

        Returns:
            Cancellation status.
        """
        deployment = self.get_deployment(deployment_id)
        endpoint_name = deployment["endpoint_name"]

        logger.info(
            "Cancelling deployment",
            deployment_id=deployment_id,
            reason=reason,
        )

        # Set canary weight to 0
        canary_variant = deployment["canary_variant"]["variant_name"]
        current_variant = deployment["current_variant"]["variant_name"]

        self.clients.sagemaker.update_endpoint_weights_and_capacities(
            EndpointName=endpoint_name,
            DesiredWeightsAndCapacities=[
                {"VariantName": current_variant, "DesiredWeight": 1.0},
                {"VariantName": canary_variant, "DesiredWeight": 0.0},
            ],
        )

        self.update_deployment_status(deployment_id, DeploymentStatus.FAILED)

        return {
            "endpoint_name": endpoint_name,
            "status": "cancelled",
        }

    def mark_deployment_complete(self, deployment_id: str) -> None:
        """Mark deployment as complete.

        Args:
            deployment_id: Deployment identifier.
        """
        self.update_deployment_status(deployment_id, DeploymentStatus.COMPLETED)

    def record_event(self, event: TrafficShiftEvent) -> None:
        """Record a traffic shift event.

        Args:
            event: Traffic shift event to record.
        """
        table = self.clients.dynamodb_resource.Table(self._events_table)
        table.put_item(Item={
            "deployment_id": event.deployment_id,
            "event_id": event.event_id,
            "event_type": "TRAFFIC_SHIFT",
            "from_weights": event.from_weights,
            "to_weights": event.to_weights,
            "reason": event.reason,
            "triggered_by": event.triggered_by,
            "timestamp": event.timestamp.isoformat(),
        })

    def record_rollback_event(self, event: RollbackEvent) -> None:
        """Record a rollback event.

        Args:
            event: Rollback event to record.
        """
        table = self.clients.dynamodb_resource.Table(self._events_table)
        table.put_item(Item={
            "deployment_id": event.deployment_id,
            "event_id": event.event_id,
            "event_type": "ROLLBACK",
            "reason": event.reason,
            "automatic": event.automatic,
            "triggered_by": event.triggered_by,
            "metrics_snapshot": {
                "error_rate": event.metrics_snapshot.error_rate,
                "p99_latency_ms": event.metrics_snapshot.model_latency_p99_ms,
                "invocation_count": event.metrics_snapshot.invocation_count,
            },
            "timestamp": event.timestamp.isoformat(),
        })

    def _describe_endpoint(self, endpoint_name: str) -> dict[str, Any]:
        """Describe SageMaker endpoint.

        Args:
            endpoint_name: Endpoint name.

        Returns:
            Endpoint description.

        Raises:
            EndpointNotFoundError: If endpoint doesn't exist.
        """
        try:
            return self.clients.sagemaker.describe_endpoint(
                EndpointName=endpoint_name
            )
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "ValidationError":
                raise EndpointNotFoundError(
                    f"Endpoint not found: {endpoint_name}",
                    endpoint_name=endpoint_name,
                )
            raise

    def _store_deployment(self, config: DeploymentConfig) -> None:
        """Store deployment record in DynamoDB.

        Args:
            config: Deployment configuration.
        """
        table = self.clients.dynamodb_resource.Table(self._deployments_table)
        table.put_item(Item={
            "deployment_id": config.deployment_id,
            "endpoint_name": config.endpoint_name,
            "status": config.status.value,
            "current_variant": config.current_variant.model_dump(),
            "canary_variant": config.canary_variant.model_dump(),
            "traffic_config": config.traffic_config.model_dump(),
            "auto_rollback_enabled": config.auto_rollback_enabled,
            "latency_threshold_ms": str(config.latency_threshold_ms),
            "error_rate_threshold": str(config.error_rate_threshold),
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
        })
