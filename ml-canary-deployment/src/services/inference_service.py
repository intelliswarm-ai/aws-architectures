"""Service for real-time SageMaker endpoint inference."""

import time
from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import AWSClients
from src.common.config import Settings
from src.common.exceptions import (
    EndpointNotFoundError,
    InferenceError,
    RetryableError,
    ThrottlingError,
    VariantNotFoundError,
)
from src.common.models import ContentType, InferenceRequest
from src.common.utils import json_deserialize, json_serialize

logger = Logger()


class InferenceService:
    """Service for invoking SageMaker endpoints for real-time inference."""

    def __init__(self, clients: AWSClients, settings: Settings):
        """Initialize inference service.

        Args:
            clients: AWS clients instance.
            settings: Application settings.
        """
        self.clients = clients
        self.settings = settings
        self._endpoint_name = settings.sagemaker_endpoint_name

    def invoke_endpoint(
        self,
        request: InferenceRequest,
        endpoint_name: str | None = None,
    ) -> dict[str, Any]:
        """Invoke SageMaker endpoint for real-time inference.

        SageMaker automatically routes the request to a production variant
        based on configured traffic weights.

        Args:
            request: Inference request with features.
            endpoint_name: Optional endpoint name override.

        Returns:
            Dictionary with predictions, variant name, and latency.

        Raises:
            InferenceError: On model inference errors.
            EndpointNotFoundError: If endpoint doesn't exist.
            RetryableError: On transient failures.
        """
        endpoint = endpoint_name or self._endpoint_name
        start_time = time.perf_counter()

        logger.info(
            "Invoking SageMaker endpoint",
            endpoint_name=endpoint,
            request_id=request.request_id,
            user_id=request.user_id,
            target_variant=request.target_variant,
        )

        try:
            # Prepare request payload
            payload = self._prepare_payload(request)

            # Build invocation parameters
            invoke_params = {
                "EndpointName": endpoint,
                "Body": payload,
                "ContentType": request.content_type.value,
                "Accept": "application/json",
            }

            # Add target variant if specified (for A/B testing)
            if request.target_variant:
                invoke_params["TargetVariant"] = request.target_variant

            # Invoke endpoint
            response = self.clients.sagemaker_runtime.invoke_endpoint(**invoke_params)

            # Calculate latency
            model_latency_ms = (time.perf_counter() - start_time) * 1000

            # Parse response
            predictions = self._parse_response(response)
            variant_name = response.get("InvokedProductionVariant", "unknown")

            logger.info(
                "Inference successful",
                request_id=request.request_id,
                variant_name=variant_name,
                model_latency_ms=model_latency_ms,
            )

            return {
                "predictions": predictions,
                "variant_name": variant_name,
                "model_latency_ms": model_latency_ms,
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            error_message = e.response.get("Error", {}).get("Message", str(e))

            if error_code == "ValidationError":
                if "endpoint" in error_message.lower():
                    raise EndpointNotFoundError(
                        f"Endpoint not found: {endpoint}",
                        endpoint_name=endpoint,
                    )
                if "variant" in error_message.lower():
                    raise VariantNotFoundError(
                        f"Variant not found: {request.target_variant}",
                        endpoint_name=endpoint,
                    )

            if error_code == "ModelError":
                raise InferenceError(
                    f"Model inference error: {error_message}",
                    variant_name=request.target_variant,
                    request_id=request.request_id,
                    endpoint_name=endpoint,
                )

            if error_code == "ThrottlingException":
                raise ThrottlingError(
                    "Endpoint throttled, retry later",
                    endpoint_name=endpoint,
                    retry_after_seconds=5,
                )

            if error_code in ("ServiceUnavailable", "InternalFailure"):
                raise RetryableError(
                    f"Transient error: {error_message}",
                    endpoint_name=endpoint,
                    retry_after_seconds=10,
                )

            raise InferenceError(
                f"Endpoint invocation failed: {error_message}",
                request_id=request.request_id,
                endpoint_name=endpoint,
                details={"error_code": error_code},
            )

        except Exception as e:
            logger.exception("Unexpected inference error", request_id=request.request_id)
            raise InferenceError(
                f"Unexpected error during inference: {e}",
                request_id=request.request_id,
                endpoint_name=endpoint,
            )

    def invoke_with_variant(
        self,
        request: InferenceRequest,
        variant_name: str,
        endpoint_name: str | None = None,
    ) -> dict[str, Any]:
        """Invoke a specific variant for testing purposes.

        Args:
            request: Inference request.
            variant_name: Target variant name.
            endpoint_name: Optional endpoint name override.

        Returns:
            Dictionary with predictions and latency.
        """
        request.target_variant = variant_name
        return self.invoke_endpoint(request, endpoint_name)

    def _prepare_payload(self, request: InferenceRequest) -> bytes:
        """Prepare request payload for SageMaker endpoint.

        Args:
            request: Inference request.

        Returns:
            Serialized payload bytes.
        """
        payload_data = {
            "user_id": request.user_id,
            "features": request.features,
            "request_id": request.request_id,
        }

        if request.content_type == ContentType.JSON:
            return json_serialize(payload_data).encode("utf-8")
        elif request.content_type == ContentType.CSV:
            # Convert features to CSV format
            feature_values = list(request.features.values())
            return ",".join(str(v) for v in feature_values).encode("utf-8")
        else:
            return json_serialize(payload_data).encode("utf-8")

    def _parse_response(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        """Parse SageMaker endpoint response.

        Args:
            response: Raw SageMaker response.

        Returns:
            List of prediction dictionaries.
        """
        body = response["Body"].read()

        try:
            data = json_deserialize(body)

            # Handle different response formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                if "predictions" in data:
                    return data["predictions"]
                return [data]
            else:
                return [{"prediction": data}]

        except Exception as e:
            logger.warning("Failed to parse response as JSON", error=str(e))
            return [{"raw_response": body.decode("utf-8", errors="replace")}]

    def check_endpoint_health(self, endpoint_name: str | None = None) -> dict[str, Any]:
        """Check if endpoint is healthy and serving traffic.

        Args:
            endpoint_name: Optional endpoint name override.

        Returns:
            Health check result.
        """
        endpoint = endpoint_name or self._endpoint_name

        try:
            response = self.clients.sagemaker.describe_endpoint(
                EndpointName=endpoint
            )

            status = response.get("EndpointStatus", "Unknown")
            variants = response.get("ProductionVariants", [])

            variant_health = {}
            for variant in variants:
                variant_health[variant["VariantName"]] = {
                    "status": variant.get("CurrentInstanceCount", 0) > 0,
                    "instance_count": variant.get("CurrentInstanceCount", 0),
                    "desired_instance_count": variant.get("DesiredInstanceCount", 0),
                    "weight": variant.get("CurrentWeight", 0.0),
                }

            return {
                "endpoint_name": endpoint,
                "status": status,
                "healthy": status == "InService",
                "variants": variant_health,
            }

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "ValidationError":
                return {
                    "endpoint_name": endpoint,
                    "status": "NotFound",
                    "healthy": False,
                    "variants": {},
                }
            raise
