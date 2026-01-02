"""Service for parsing and processing call transcripts."""

import json
from datetime import datetime
from typing import Any

import boto3
from aws_lambda_powertools import Logger

from common.config import get_settings
from common.exceptions import TranscriptParseError
from common.models import CallTranscript, Speaker, TranscriptSegment

logger = Logger()
settings = get_settings()


def get_s3_client():
    """Get S3 client."""
    return boto3.client("s3", region_name=settings.aws_region)


class TranscriptService:
    """Service for transcript parsing and processing."""

    def __init__(self, s3_client=None):
        self.s3_client = s3_client or get_s3_client()

    def parse_transcript_from_s3(
        self,
        bucket: str,
        key: str,
    ) -> CallTranscript:
        """Parse transcript from S3 object."""
        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read().decode("utf-8")
            data = json.loads(content)
            return self.parse_transcript(data, key)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in transcript file: {key}")
            raise TranscriptParseError(
                f"Invalid JSON format: {e}",
                file_key=key,
            )
        except Exception as e:
            logger.error(f"Error reading transcript from S3: {e}")
            raise TranscriptParseError(
                f"Failed to read transcript: {e}",
                file_key=key,
            )

    def parse_transcript(
        self,
        data: dict[str, Any],
        source_key: str | None = None,
    ) -> CallTranscript:
        """Parse transcript from dictionary data."""
        try:
            # Parse timestamp
            timestamp = data.get("timestamp")
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            elif timestamp is None:
                timestamp = datetime.utcnow()

            # Parse segments
            segments = []
            for seg_data in data.get("segments", []):
                speaker_str = seg_data.get("speaker", "UNKNOWN").upper()
                try:
                    speaker = Speaker(speaker_str)
                except ValueError:
                    speaker = Speaker.UNKNOWN

                segments.append(
                    TranscriptSegment(
                        speaker=speaker,
                        start_time=float(seg_data.get("startTime", 0)),
                        end_time=float(seg_data.get("endTime", 0)),
                        text=seg_data.get("text", ""),
                    )
                )

            return CallTranscript(
                call_id=data.get("callId", data.get("call_id", "")),
                timestamp=timestamp,
                duration=int(data.get("duration", 0)),
                agent_id=data.get("agentId", data.get("agent_id", "")),
                agent_name=data.get("agentName", data.get("agent_name")),
                customer_id=data.get("customerId", data.get("customer_id", "")),
                customer_phone=data.get("customerPhone", data.get("customer_phone")),
                queue_name=data.get("queueName", data.get("queue_name")),
                language=data.get("language", "en"),
                segments=segments,
                metadata=data.get("metadata", {}),
            )
        except Exception as e:
            logger.error(f"Error parsing transcript data: {e}")
            raise TranscriptParseError(
                f"Failed to parse transcript: {e}",
                file_key=source_key,
            )

    def prepare_for_comprehend(
        self,
        transcripts: list[CallTranscript],
    ) -> str:
        """Prepare transcripts for Comprehend batch input (one doc per line)."""
        lines = []
        for transcript in transcripts:
            text = transcript.get_full_text()
            # Comprehend expects clean text, one document per line
            clean_text = " ".join(text.split())  # Normalize whitespace
            lines.append(clean_text)
        return "\n".join(lines)

    def upload_for_comprehend(
        self,
        transcripts: list[CallTranscript],
        bucket: str,
        key: str,
    ) -> str:
        """Upload transcripts to S3 for Comprehend batch processing."""
        content = self.prepare_for_comprehend(transcripts)

        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/plain",
            )

            s3_uri = f"s3://{bucket}/{key}"
            logger.info(f"Uploaded {len(transcripts)} transcripts to {s3_uri}")
            return s3_uri

        except Exception as e:
            logger.error(f"Error uploading to S3: {e}")
            raise TranscriptParseError(
                f"Failed to upload transcripts: {e}",
            )

    def list_transcripts(
        self,
        bucket: str,
        prefix: str | None = None,
        max_keys: int = 1000,
    ) -> list[str]:
        """List transcript files in S3 bucket."""
        prefix = prefix or settings.transcripts_prefix

        try:
            response = self.s3_client.list_objects_v2(
                Bucket=bucket,
                Prefix=prefix,
                MaxKeys=max_keys,
            )

            keys = []
            for obj in response.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".json"):
                    keys.append(key)

            return keys

        except Exception as e:
            logger.error(f"Error listing transcripts: {e}")
            return []

    def validate_transcript(self, transcript: CallTranscript) -> list[str]:
        """Validate transcript data, return list of validation errors."""
        errors = []

        if not transcript.call_id:
            errors.append("Missing call_id")

        if not transcript.agent_id:
            errors.append("Missing agent_id")

        if not transcript.customer_id:
            errors.append("Missing customer_id")

        if not transcript.segments:
            errors.append("No segments in transcript")

        if transcript.duration < 0:
            errors.append("Invalid duration")

        for i, segment in enumerate(transcript.segments):
            if not segment.text.strip():
                errors.append(f"Empty text in segment {i}")
            if segment.end_time < segment.start_time:
                errors.append(f"Invalid time range in segment {i}")

        return errors
