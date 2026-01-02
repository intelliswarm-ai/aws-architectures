"""Utility functions for the enterprise serverless platform."""

import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

import orjson


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix.

    Args:
        prefix: Optional prefix for the ID

    Returns:
        Unique ID string
    """
    unique_id = str(uuid.uuid4())
    return f"{prefix}{unique_id}" if prefix else unique_id


def generate_request_id() -> str:
    """Generate a request ID for tracing."""
    return generate_id("req-")


def generate_event_id() -> str:
    """Generate an event ID for audit logging."""
    return generate_id("evt-")


def utc_now() -> datetime:
    """Get current UTC timestamp."""
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    """Get current UTC timestamp as ISO string."""
    return utc_now().isoformat()


def to_iso_string(dt: datetime) -> str:
    """Convert datetime to ISO string."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat()


def from_iso_string(iso_string: str) -> datetime:
    """Parse ISO string to datetime."""
    return datetime.fromisoformat(iso_string.replace("Z", "+00:00"))


def json_dumps(obj: Any) -> str:
    """Fast JSON serialization using orjson."""
    return orjson.dumps(obj).decode("utf-8")


def json_loads(data: str | bytes) -> Any:
    """Fast JSON deserialization using orjson."""
    return orjson.loads(data)


def hash_string(value: str) -> str:
    """Create a SHA-256 hash of a string.

    Args:
        value: String to hash

    Returns:
        Hex-encoded hash
    """
    return hashlib.sha256(value.encode()).hexdigest()


def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive data, showing only last N characters.

    Args:
        value: Value to mask
        visible_chars: Number of characters to show at the end

    Returns:
        Masked string
    """
    if len(value) <= visible_chars:
        return "*" * len(value)
    return "*" * (len(value) - visible_chars) + value[-visible_chars:]


def safe_get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    """Safely get a nested dictionary value.

    Args:
        data: Dictionary to search
        *keys: Keys to traverse
        default: Default value if not found

    Returns:
        The value or default
    """
    current = data
    for key in keys:
        if not isinstance(current, dict):
            return default
        current = current.get(key, default)
        if current is default:
            return default
    return current


def parse_api_gateway_event(event: dict[str, Any]) -> dict[str, Any]:
    """Parse API Gateway event into a normalized format.

    Args:
        event: Raw API Gateway event

    Returns:
        Normalized event dictionary
    """
    body = event.get("body")
    if body and event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    parsed_body = None
    if body:
        content_type = (event.get("headers") or {}).get("Content-Type", "")
        if "application/json" in content_type.lower():
            try:
                parsed_body = json_loads(body)
            except (json.JSONDecodeError, orjson.JSONDecodeError):
                parsed_body = body
        else:
            parsed_body = body

    return {
        "method": event.get("httpMethod", ""),
        "path": event.get("path", ""),
        "path_parameters": event.get("pathParameters") or {},
        "query_parameters": event.get("queryStringParameters") or {},
        "headers": event.get("headers") or {},
        "body": parsed_body,
        "raw_body": body,
        "is_base64_encoded": event.get("isBase64Encoded", False),
        "request_context": event.get("requestContext") or {},
        "stage_variables": event.get("stageVariables") or {},
    }


def build_api_response(
    status_code: int,
    body: Any,
    headers: dict[str, str] | None = None,
    cors: bool = True,
) -> dict[str, Any]:
    """Build an API Gateway response.

    Args:
        status_code: HTTP status code
        body: Response body (will be JSON serialized)
        headers: Additional headers
        cors: Include CORS headers

    Returns:
        API Gateway response dictionary
    """
    response_headers = {
        "Content-Type": "application/json",
    }

    if cors:
        response_headers.update({
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key",
            "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        })

    if headers:
        response_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": response_headers,
        "body": json_dumps(body) if not isinstance(body, str) else body,
    }


def success_response(data: Any = None, message: str | None = None) -> dict[str, Any]:
    """Build a successful API response.

    Args:
        data: Response data
        message: Optional message

    Returns:
        API Gateway response with 200 status
    """
    body = {
        "success": True,
        "data": data,
        "timestamp": utc_now_iso(),
    }
    if message:
        body["message"] = message

    return build_api_response(200, body)


def error_response(
    status_code: int,
    error: str,
    message: str,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an error API response.

    Args:
        status_code: HTTP status code
        error: Error code
        message: Error message
        details: Additional error details

    Returns:
        API Gateway response with error
    """
    body: dict[str, Any] = {
        "success": False,
        "error": error,
        "message": message,
        "timestamp": utc_now_iso(),
    }
    if details:
        body["details"] = details

    return build_api_response(status_code, body)


def chunk_list(lst: list[Any], chunk_size: int) -> list[list[Any]]:
    """Split a list into chunks.

    Args:
        lst: List to split
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [lst[i : i + chunk_size] for i in range(0, len(lst), chunk_size)]


def flatten_dict(
    d: dict[str, Any],
    parent_key: str = "",
    separator: str = ".",
) -> dict[str, Any]:
    """Flatten a nested dictionary.

    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix
        separator: Key separator

    Returns:
        Flattened dictionary
    """
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{separator}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, separator).items())
        else:
            items.append((new_key, v))
    return dict(items)
