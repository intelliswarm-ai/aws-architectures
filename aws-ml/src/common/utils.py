"""Utility functions for document processing."""

import hashlib
import mimetypes
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote_plus

import orjson

from .models import DocumentType


def generate_document_id() -> str:
    """Generate a unique document ID."""
    return str(uuid.uuid4())


def generate_idempotency_key(document_id: str, operation: str) -> str:
    """Generate an idempotency key for an operation."""
    return hashlib.sha256(f"{document_id}:{operation}".encode()).hexdigest()[:32]


def detect_document_type(key: str, content_type: str | None = None) -> DocumentType:
    """Detect document type from S3 key or content type."""
    # Get extension from key
    ext = Path(key).suffix.lower()

    # PDF
    if ext == ".pdf" or content_type == "application/pdf":
        return DocumentType.PDF

    # Images
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".webp"}
    if ext in image_extensions or (content_type and content_type.startswith("image/")):
        return DocumentType.IMAGE

    # Audio
    audio_extensions = {".mp3", ".wav", ".flac", ".ogg", ".m4a", ".wma", ".aac"}
    if ext in audio_extensions or (content_type and content_type.startswith("audio/")):
        return DocumentType.AUDIO

    # Text
    text_extensions = {".txt", ".md", ".csv", ".json", ".xml", ".html"}
    if ext in text_extensions or (content_type and content_type.startswith("text/")):
        return DocumentType.TEXT

    return DocumentType.UNKNOWN


def parse_s3_event(event: dict[str, Any]) -> list[dict[str, str]]:
    """Parse S3 event notification and extract bucket/key pairs."""
    records = []
    for record in event.get("Records", []):
        if record.get("eventSource") == "aws:s3":
            bucket = record["s3"]["bucket"]["name"]
            key = unquote_plus(record["s3"]["object"]["key"])
            records.append({"bucket": bucket, "key": key})
    return records


def get_content_type(key: str) -> str:
    """Get MIME type for a file."""
    mime_type, _ = mimetypes.guess_type(key)
    return mime_type or "application/octet-stream"


def truncate_text(text: str, max_length: int = 10000) -> str:
    """Truncate text to maximum length while preserving word boundaries."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length].rsplit(" ", 1)[0]
    return truncated + "..."


def clean_text(text: str) -> str:
    """Clean extracted text by removing extra whitespace."""
    # Replace multiple whitespace with single space
    text = re.sub(r"\s+", " ", text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text


def json_serialize(obj: Any) -> str:
    """Serialize object to JSON string."""
    return orjson.dumps(obj, default=_json_default).decode("utf-8")


def json_deserialize(data: str | bytes) -> Any:
    """Deserialize JSON string to object."""
    return orjson.loads(data)


def _json_default(obj: Any) -> Any:
    """Default JSON serializer for unsupported types."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def calculate_cost_estimate(
    textract_pages: int = 0,
    comprehend_units: int = 0,
    rekognition_images: int = 0,
    transcribe_minutes: float = 0,
    sagemaker_invocations: int = 0,
    bedrock_input_tokens: int = 0,
    bedrock_output_tokens: int = 0,
) -> dict[str, float]:
    """Estimate processing costs (approximate, check AWS pricing)."""
    # Approximate pricing (USD) - varies by region
    costs = {
        "textract": textract_pages * 0.0015,  # Per page
        "comprehend": comprehend_units * 0.0001,  # Per unit (100 chars)
        "rekognition": rekognition_images * 0.001,  # Per image
        "transcribe": transcribe_minutes * 0.024,  # Per minute
        "sagemaker": sagemaker_invocations * 0.0001,  # Approximate
        "bedrock_input": bedrock_input_tokens * 0.000003,  # Claude 3 Sonnet
        "bedrock_output": bedrock_output_tokens * 0.000015,  # Claude 3 Sonnet
    }
    costs["total"] = sum(costs.values())
    return costs


def mask_pii(text: str, entities: list[dict[str, Any]]) -> str:
    """Mask PII entities in text."""
    # Sort entities by offset in reverse order to maintain positions
    sorted_entities = sorted(entities, key=lambda e: e.get("begin_offset", 0), reverse=True)

    masked = text
    for entity in sorted_entities:
        begin = entity.get("begin_offset", 0)
        end = entity.get("end_offset", 0)
        entity_type = entity.get("entity_type", "PII")
        if begin < end <= len(masked):
            masked = masked[:begin] + f"[{entity_type}]" + masked[end:]

    return masked
