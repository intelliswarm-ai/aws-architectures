"""Service for managing traffic distribution between SageMaker variants."""

from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import AWSClients
from src.common.config import Settings
from src.common.exceptions import (
    EndpointNotFoundError,
    TrafficShiftError,
    VariantNotFoundError,
)

logger = Logger()


class TrafficService:
    """Service for managing traffic splitting between production variants."""

    def __init__(self, clients: AWSClients, settings: Settings):
        """Initialize traffic service.

        Args:
            clients: AWS clients instance.
            settings: Application settings.
        """
        self.clients = clients
        self.settings = settings

    def get_variant_weights(self, endpoint_name: str) -> dict[str, float]:
        """Get current traffic weights for all variants.

        Args:
            endpoint_name: SageMaker endpoint name.

        Returns:
            Dictionary mapping variant names to weights.

        Raises:
            EndpointNotFoundError: If endpoint doesn't exist.
        """
        try:
            response = self.clients.sagemaker.describe_endpoint(
                EndpointName=endpoint_name
            )

            weights = {}
            for variant in response.get("ProductionVariants", []):
                weights[variant["VariantName"]] = variant.get("CurrentWeight", 0.0)

            logger.debug(
                "Retrieved variant weights",
                endpoint_name=endpoint_name,
                weights=weights,
            )

            return weights

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ValidationError":
                raise EndpointNotFoundError(
                    f"Endpoint not found: {endpoint_name}",
                    endpoint_name=endpoint_name,
                )
            raise TrafficShiftError(
                f"Failed to get variant weights: {e}",
                endpoint_name=endpoint_name,
            )

    def update_variant_weights(
        self,
        endpoint_name: str,
        weights: dict[str, float],
    ) -> dict[str, Any]:
        """Update traffic weights for variants using UpdateEndpointWeightsAndCapacities.

        This is the key API for canary deployments - it allows changing traffic
        distribution without endpoint downtime.

        Args:
            endpoint_name: SageMaker endpoint name.
            weights: Dictionary mapping variant names to desired weights (0.0-1.0).

        Returns:
            Update result with new weights.

        Raises:
            TrafficShiftError: On update failure.
            VariantNotFoundError: If a variant doesn't exist.
        """
        logger.info(
            "Updating variant weights",
            endpoint_name=endpoint_name,
            weights=weights,
        )

        try:
            # Build desired weights and capacities
            desired_weights = [
                {
                    "VariantName": variant_name,
                    "DesiredWeight": weight,
                }
                for variant_name, weight in weights.items()
            ]

            # Call SageMaker API
            self.clients.sagemaker.update_endpoint_weights_and_capacities(
                EndpointName=endpoint_name,
                DesiredWeightsAndCapacities=desired_weights,
            )

            logger.info(
                "Variant weights updated successfully",
                endpoint_name=endpoint_name,
                new_weights=weights,
            )

            return {
                "status": "updated",
                "endpoint_name": endpoint_name,
                "weights": weights,
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "ValidationError":
                if "endpoint" in error_message.lower():
                    raise EndpointNotFoundError(
                        f"Endpoint not found: {endpoint_name}",
                        endpoint_name=endpoint_name,
                    )
                if "variant" in error_message.lower():
                    raise VariantNotFoundError(
                        f"Variant not found in endpoint: {error_message}",
                        endpoint_name=endpoint_name,
                    )

            raise TrafficShiftError(
                f"Failed to update weights: {error_message}",
                endpoint_name=endpoint_name,
                target_weights=weights,
            )

    def shift_traffic(
        self,
        endpoint_name: str,
        from_variant: str,
        to_variant: str,
        shift_amount: float,
    ) -> dict[str, Any]:
        """Shift traffic between two variants.

        Args:
            endpoint_name: SageMaker endpoint name.
            from_variant: Source variant to reduce traffic from.
            to_variant: Target variant to increase traffic to.
            shift_amount: Amount of traffic to shift (0.0-1.0).

        Returns:
            Shift result with new weights.
        """
        # Get current weights
        current_weights = self.get_variant_weights(endpoint_name)

        from_weight = current_weights.get(from_variant, 0.0)
        to_weight = current_weights.get(to_variant, 0.0)

        # Calculate new weights
        new_from_weight = max(from_weight - shift_amount, 0.0)
        new_to_weight = min(to_weight + shift_amount, 1.0)

        new_weights = {
            from_variant: new_from_weight,
            to_variant: new_to_weight,
        }

        # Include any other variants with their current weights
        for variant, weight in current_weights.items():
            if variant not in new_weights:
                new_weights[variant] = weight

        return self.update_variant_weights(endpoint_name, new_weights)

    def set_variant_to_full_traffic(
        self,
        endpoint_name: str,
        variant_name: str,
    ) -> dict[str, Any]:
        """Route 100% traffic to a specific variant.

        Used for rollback or deployment completion.

        Args:
            endpoint_name: SageMaker endpoint name.
            variant_name: Variant to receive all traffic.

        Returns:
            Update result.
        """
        current_weights = self.get_variant_weights(endpoint_name)

        # Set target to 100%, all others to 0%
        new_weights = {name: 0.0 for name in current_weights}
        new_weights[variant_name] = 1.0

        return self.update_variant_weights(endpoint_name, new_weights)

    def get_variant_instances(self, endpoint_name: str) -> dict[str, dict[str, int]]:
        """Get instance counts for all variants.

        Args:
            endpoint_name: SageMaker endpoint name.

        Returns:
            Dictionary mapping variant names to instance info.
        """
        try:
            response = self.clients.sagemaker.describe_endpoint(
                EndpointName=endpoint_name
            )

            instances = {}
            for variant in response.get("ProductionVariants", []):
                instances[variant["VariantName"]] = {
                    "current_count": variant.get("CurrentInstanceCount", 0),
                    "desired_count": variant.get("DesiredInstanceCount", 0),
                }

            return instances

        except ClientError as e:
            raise TrafficShiftError(
                f"Failed to get variant instances: {e}",
                endpoint_name=endpoint_name,
            )

    def update_variant_capacity(
        self,
        endpoint_name: str,
        variant_name: str,
        desired_instance_count: int,
    ) -> dict[str, Any]:
        """Update instance count for a variant.

        Args:
            endpoint_name: SageMaker endpoint name.
            variant_name: Variant to scale.
            desired_instance_count: Target instance count.

        Returns:
            Update result.
        """
        logger.info(
            "Updating variant capacity",
            endpoint_name=endpoint_name,
            variant_name=variant_name,
            desired_count=desired_instance_count,
        )

        try:
            self.clients.sagemaker.update_endpoint_weights_and_capacities(
                EndpointName=endpoint_name,
                DesiredWeightsAndCapacities=[
                    {
                        "VariantName": variant_name,
                        "DesiredInstanceCount": desired_instance_count,
                    }
                ],
            )

            return {
                "status": "scaling",
                "variant_name": variant_name,
                "desired_instance_count": desired_instance_count,
            }

        except ClientError as e:
            raise TrafficShiftError(
                f"Failed to update capacity: {e}",
                endpoint_name=endpoint_name,
            )

    def validate_weights(self, weights: dict[str, float]) -> bool:
        """Validate that weights sum to approximately 1.0.

        Args:
            weights: Dictionary of variant weights.

        Returns:
            True if valid, False otherwise.
        """
        total = sum(weights.values())
        return 0.99 <= total <= 1.01
