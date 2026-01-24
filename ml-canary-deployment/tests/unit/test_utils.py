"""Unit tests for utility functions."""

import pytest

from src.common.utils import (
    calculate_error_rate,
    format_duration,
    format_variant_name,
    generate_deployment_id,
    generate_request_id,
    normalize_weights,
    safe_get,
)


class TestGenerateIds:
    """Tests for ID generation functions."""

    def test_generate_deployment_id(self) -> None:
        """Test deployment ID generation."""
        deployment_id = generate_deployment_id()
        assert deployment_id.startswith("deploy-")
        assert len(deployment_id) > 15

    def test_generate_request_id(self) -> None:
        """Test request ID generation."""
        request_id = generate_request_id()
        assert request_id.startswith("req-")
        assert len(request_id) > 10

    def test_unique_ids(self) -> None:
        """Test that generated IDs are unique."""
        ids = [generate_deployment_id() for _ in range(100)]
        assert len(ids) == len(set(ids))


class TestNormalizeWeights:
    """Tests for weight normalization."""

    def test_normalize_weights(self) -> None:
        """Test weight normalization."""
        weights = {"a": 2, "b": 3}
        normalized = normalize_weights(weights)
        assert normalized["a"] == 0.4
        assert normalized["b"] == 0.6

    def test_already_normalized(self) -> None:
        """Test weights that are already normalized."""
        weights = {"a": 0.7, "b": 0.3}
        normalized = normalize_weights(weights)
        assert abs(normalized["a"] - 0.7) < 0.01
        assert abs(normalized["b"] - 0.3) < 0.01

    def test_zero_weights(self) -> None:
        """Test handling of zero weights."""
        weights = {"a": 0, "b": 0}
        normalized = normalize_weights(weights)
        assert normalized == weights


class TestCalculateErrorRate:
    """Tests for error rate calculation."""

    def test_calculate_error_rate(self) -> None:
        """Test error rate calculation."""
        rate = calculate_error_rate(1000, 5, 5)
        assert rate == 0.01

    def test_zero_invocations(self) -> None:
        """Test with zero invocations."""
        rate = calculate_error_rate(0, 0, 0)
        assert rate == 0.0

    def test_high_error_rate(self) -> None:
        """Test high error rate capping at 1.0."""
        rate = calculate_error_rate(100, 50, 60)
        assert rate == 1.0


class TestFormatVariantName:
    """Tests for variant name formatting."""

    def test_format_variant_name(self) -> None:
        """Test variant name formatting."""
        name = format_variant_name("my-model", "v1.2.3")
        assert name == "my-model-v1-2-3"

    def test_special_characters(self) -> None:
        """Test handling of special characters."""
        name = format_variant_name("model@test!", "v1")
        assert "@" not in name
        assert "!" not in name

    def test_max_length(self) -> None:
        """Test that name is truncated to max length."""
        long_name = "a" * 100
        name = format_variant_name(long_name, "v1")
        assert len(name) <= 63


class TestSafeGet:
    """Tests for safe dictionary access."""

    def test_safe_get_simple(self) -> None:
        """Test simple key access."""
        data = {"a": 1}
        assert safe_get(data, "a") == 1

    def test_safe_get_nested(self) -> None:
        """Test nested key access."""
        data = {"a": {"b": {"c": 3}}}
        assert safe_get(data, "a", "b", "c") == 3

    def test_safe_get_missing(self) -> None:
        """Test missing key with default."""
        data = {"a": 1}
        assert safe_get(data, "b", default="default") == "default"

    def test_safe_get_nested_missing(self) -> None:
        """Test nested missing key."""
        data = {"a": {"b": 1}}
        assert safe_get(data, "a", "c", "d", default=None) is None


class TestFormatDuration:
    """Tests for duration formatting."""

    def test_format_seconds(self) -> None:
        """Test formatting seconds."""
        assert format_duration(30) == "30.0s"

    def test_format_minutes(self) -> None:
        """Test formatting minutes."""
        assert format_duration(90) == "1.5m"

    def test_format_hours(self) -> None:
        """Test formatting hours."""
        assert format_duration(7200) == "2.0h"
