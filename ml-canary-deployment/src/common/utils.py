"""Utility functions for ML Canary Deployment system."""

import hashlib
import json
import time
import uuid
from datetime import datetime
from typing import Any

import orjson


def generate_deployment_id() -> str:
    """Generate a unique deployment identifier.

    Returns:
        Unique deployment ID in format 'deploy-{timestamp}-{uuid}'.
    """
    timestamp = int(time.time())
    short_uuid = uuid.uuid4().hex[:8]
    return f"deploy-{timestamp}-{short_uuid}"


def generate_request_id() -> str:
    """Generate a unique request identifier.

    Returns:
        Unique request ID in format 'req-{uuid}'.
    """
    return f"req-{uuid.uuid4().hex}"


def generate_event_id() -> str:
    """Generate a unique event identifier.

    Returns:
        Unique event ID in format 'evt-{uuid}'.
    """
    return f"evt-{uuid.uuid4().hex}"


def json_serialize(obj: Any) -> str:
    """Serialize object to JSON string using orjson for performance.

    Args:
        obj: Object to serialize.

    Returns:
        JSON string representation.
    """
    return orjson.dumps(obj, default=_json_default).decode("utf-8")


def json_deserialize(data: str | bytes) -> Any:
    """Deserialize JSON string to object using orjson.

    Args:
        data: JSON string or bytes to deserialize.

    Returns:
        Deserialized Python object.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    return orjson.loads(data)


def _json_default(obj: Any) -> Any:
    """Default JSON serializer for non-standard types.

    Args:
        obj: Object to serialize.

    Returns:
        Serializable representation.

    Raises:
        TypeError: If object is not serializable.
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def calculate_model_hash(model_data: bytes) -> str:
    """Calculate SHA-256 hash of model data.

    Args:
        model_data: Model binary data.

    Returns:
        Hexadecimal hash string.
    """
    return hashlib.sha256(model_data).hexdigest()


def normalize_weights(weights: dict[str, float]) -> dict[str, float]:
    """Normalize traffic weights to sum to 1.0.

    Args:
        weights: Dictionary of variant names to weights.

    Returns:
        Normalized weights dictionary.
    """
    total = sum(weights.values())
    if total == 0:
        return weights
    return {k: v / total for k, v in weights.items()}


def calculate_error_rate(
    invocation_count: int, error_4xx: int, error_5xx: int
) -> float:
    """Calculate error rate from invocation metrics.

    Args:
        invocation_count: Total number of invocations.
        error_4xx: Count of 4xx errors.
        error_5xx: Count of 5xx errors.

    Returns:
        Error rate as a decimal (0.0 to 1.0).
    """
    if invocation_count == 0:
        return 0.0
    total_errors = error_4xx + error_5xx
    return min(total_errors / invocation_count, 1.0)


def format_variant_name(model_name: str, version: str) -> str:
    """Format a consistent variant name from model name and version.

    Args:
        model_name: Base model name.
        version: Model version.

    Returns:
        Formatted variant name.
    """
    # Remove special characters and format consistently
    clean_name = "".join(c if c.isalnum() else "-" for c in model_name)
    clean_version = "".join(c if c.isalnum() else "-" for c in version)
    return f"{clean_name}-{clean_version}"[:63]  # Max length for variant names


def parse_sagemaker_arn(arn: str) -> dict[str, str]:
    """Parse a SageMaker ARN into its components.

    Args:
        arn: SageMaker resource ARN.

    Returns:
        Dictionary with ARN components (region, account, resource_type, resource_name).
    """
    # Format: arn:aws:sagemaker:region:account:resource-type/resource-name
    parts = arn.split(":")
    if len(parts) < 6:
        raise ValueError(f"Invalid SageMaker ARN: {arn}")

    resource_parts = parts[5].split("/")

    return {
        "region": parts[3],
        "account": parts[4],
        "resource_type": resource_parts[0],
        "resource_name": resource_parts[1] if len(resource_parts) > 1 else "",
    }


def build_endpoint_arn(
    region: str, account_id: str, endpoint_name: str
) -> str:
    """Build a SageMaker endpoint ARN.

    Args:
        region: AWS region.
        account_id: AWS account ID.
        endpoint_name: Endpoint name.

    Returns:
        SageMaker endpoint ARN.
    """
    return f"arn:aws:sagemaker:{region}:{account_id}:endpoint/{endpoint_name}"


def timestamp_to_iso(timestamp: float | int) -> str:
    """Convert Unix timestamp to ISO format string.

    Args:
        timestamp: Unix timestamp (seconds since epoch).

    Returns:
        ISO format datetime string.
    """
    return datetime.utcfromtimestamp(timestamp).isoformat() + "Z"


def iso_to_timestamp(iso_string: str) -> float:
    """Convert ISO format string to Unix timestamp.

    Args:
        iso_string: ISO format datetime string.

    Returns:
        Unix timestamp (seconds since epoch).
    """
    # Handle both with and without Z suffix
    if iso_string.endswith("Z"):
        iso_string = iso_string[:-1]
    dt = datetime.fromisoformat(iso_string)
    return dt.timestamp()


def chunk_list(lst: list, chunk_size: int) -> list[list]:
    """Split a list into chunks of specified size.

    Args:
        lst: List to split.
        chunk_size: Maximum size of each chunk.

    Returns:
        List of list chunks.
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """Safely get a nested value from a dictionary.

    Args:
        data: Dictionary to search.
        keys: Sequence of keys to traverse.
        default: Default value if key not found.

    Returns:
        Value at nested key or default.
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
        if current is default:
            return default
    return current


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human readable string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Human readable duration string.
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """Truncate a string to maximum length with suffix.

    Args:
        s: String to truncate.
        max_length: Maximum length including suffix.
        suffix: Suffix to append when truncating.

    Returns:
        Truncated string.
    """
    if len(s) <= max_length:
        return s
    return s[: max_length - len(suffix)] + suffix
