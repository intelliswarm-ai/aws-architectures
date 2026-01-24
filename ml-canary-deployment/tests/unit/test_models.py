"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from src.common.models import (
    ContentType,
    DeploymentConfig,
    DeploymentStatus,
    EndpointMetrics,
    InferenceRequest,
    InferenceResponse,
    ModelVariant,
    TrafficConfig,
)


class TestModelVariant:
    """Tests for ModelVariant model."""

    def test_valid_model_variant(self) -> None:
        """Test creating a valid ModelVariant."""
        variant = ModelVariant(
            variant_name="production",
            model_name="test-model",
            instance_type="ml.m5.xlarge",
            initial_instance_count=2,
            initial_weight=0.9,
        )
        assert variant.variant_name == "production"
        assert variant.model_name == "test-model"
        assert variant.initial_weight == 0.9

    def test_default_values(self) -> None:
        """Test default values for ModelVariant."""
        variant = ModelVariant(
            variant_name="test",
            model_name="model",
        )
        assert variant.instance_type == "ml.m5.xlarge"
        assert variant.initial_instance_count == 1
        assert variant.initial_weight == 1.0

    def test_invalid_weight(self) -> None:
        """Test that weight must be between 0 and 1."""
        with pytest.raises(ValidationError):
            ModelVariant(
                variant_name="test",
                model_name="model",
                initial_weight=1.5,
            )


class TestTrafficConfig:
    """Tests for TrafficConfig model."""

    def test_valid_traffic_config(self) -> None:
        """Test creating a valid TrafficConfig."""
        config = TrafficConfig(
            variant_weights={"production": 0.9, "canary": 0.1},
            canary_size=0.1,
            step_size=0.1,
            bake_time_minutes=10,
        )
        assert config.variant_weights["production"] == 0.9
        assert config.canary_size == 0.1

    def test_weights_must_sum_to_one(self) -> None:
        """Test that weights must sum to approximately 1.0."""
        with pytest.raises(ValidationError):
            TrafficConfig(
                variant_weights={"production": 0.5, "canary": 0.3},
            )


class TestInferenceRequest:
    """Tests for InferenceRequest model."""

    def test_valid_inference_request(self) -> None:
        """Test creating a valid InferenceRequest."""
        request = InferenceRequest(
            request_id="req-123",
            user_id="user-456",
            features={"feature1": 1.0, "feature2": 2.0},
        )
        assert request.request_id == "req-123"
        assert request.user_id == "user-456"
        assert request.content_type == ContentType.JSON

    def test_with_target_variant(self) -> None:
        """Test InferenceRequest with target variant."""
        request = InferenceRequest(
            request_id="req-123",
            user_id="user-456",
            features={"feature1": 1.0},
            target_variant="canary",
        )
        assert request.target_variant == "canary"


class TestInferenceResponse:
    """Tests for InferenceResponse model."""

    def test_valid_inference_response(self) -> None:
        """Test creating a valid InferenceResponse."""
        response = InferenceResponse(
            request_id="req-123",
            predictions=[{"score": 0.95}],
            variant_name="production",
            model_latency_ms=45.0,
            total_latency_ms=55.0,
        )
        assert response.request_id == "req-123"
        assert response.variant_name == "production"
        assert response.model_latency_ms == 45.0


class TestEndpointMetrics:
    """Tests for EndpointMetrics model."""

    def test_valid_endpoint_metrics(self) -> None:
        """Test creating valid EndpointMetrics."""
        metrics = EndpointMetrics(
            variant_name="canary",
            endpoint_name="test-endpoint",
            invocation_count=1000,
            invocation_4xx_errors=5,
            invocation_5xx_errors=2,
            model_latency_p99_ms=75.0,
            error_rate=0.007,
        )
        assert metrics.variant_name == "canary"
        assert metrics.invocation_count == 1000

    def test_is_healthy_property(self) -> None:
        """Test is_healthy property."""
        healthy_metrics = EndpointMetrics(
            variant_name="canary",
            endpoint_name="test",
            error_rate=0.005,
            model_latency_p99_ms=50.0,
        )
        assert healthy_metrics.is_healthy is True

        unhealthy_metrics = EndpointMetrics(
            variant_name="canary",
            endpoint_name="test",
            error_rate=0.02,
            model_latency_p99_ms=150.0,
        )
        assert unhealthy_metrics.is_healthy is False


class TestDeploymentConfig:
    """Tests for DeploymentConfig model."""

    def test_valid_deployment_config(
        self, sample_deployment_config: dict
    ) -> None:
        """Test creating a valid DeploymentConfig."""
        current_variant = ModelVariant(**sample_deployment_config["current_variant"])
        canary_variant = ModelVariant(**sample_deployment_config["canary_variant"])
        traffic_config = TrafficConfig(
            variant_weights={
                "production": 0.9,
                "canary": 0.1,
            }
        )

        config = DeploymentConfig(
            deployment_id="deploy-123",
            endpoint_name=sample_deployment_config["endpoint_name"],
            current_variant=current_variant,
            canary_variant=canary_variant,
            traffic_config=traffic_config,
        )

        assert config.deployment_id == "deploy-123"
        assert config.status == DeploymentStatus.PENDING
        assert config.auto_rollback_enabled is True
