"""Transcribe service for audio transcription."""

import time
import uuid
from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import ExtractionError, RetryableError
from src.common.models import ExtractionResult

logger = Logger()


class TranscribeService:
    """Service for audio transcription using Amazon Transcribe."""

    def __init__(self):
        self.settings = get_settings()
        self.clients = get_clients()

    def start_transcription(
        self,
        bucket: str,
        key: str,
        document_id: str,
        language_code: str = "en-US",
        media_format: str | None = None,
    ) -> str:
        """
        Start an asynchronous transcription job.
        Returns job name for status polling.
        """
        try:
            # Generate unique job name
            job_name = f"doc-{document_id}-{uuid.uuid4().hex[:8]}"

            # Determine media format from key if not provided
            if not media_format:
                media_format = self._detect_media_format(key)

            # Build S3 URI
            media_uri = f"s3://{bucket}/{key}"

            # Start transcription job
            self.clients.transcribe.start_transcription_job(
                TranscriptionJobName=job_name,
                LanguageCode=language_code,
                MediaFormat=media_format,
                Media={"MediaFileUri": media_uri},
                OutputBucketName=self.settings.processed_bucket,
                OutputKey=f"transcripts/{document_id}/{job_name}.json",
                Settings={
                    "ShowSpeakerLabels": True,
                    "MaxSpeakerLabels": 10,
                    "ShowAlternatives": False,
                },
            )

            logger.info(
                "Started transcription job",
                document_id=document_id,
                job_name=job_name,
                media_format=media_format,
            )
            return job_name

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code == "LimitExceededException":
                raise RetryableError(
                    f"Transcribe limit exceeded: {e}",
                    document_id=document_id,
                    retry_after_seconds=60,
                )
            raise ExtractionError(
                f"Failed to start transcription: {e}",
                document_id=document_id,
                service="transcribe",
            )

    def get_transcription_status(self, job_name: str) -> dict[str, Any]:
        """Get status of a transcription job."""
        response = self.clients.transcribe.get_transcription_job(
            TranscriptionJobName=job_name
        )
        job = response.get("TranscriptionJob", {})

        return {
            "status": job.get("TranscriptionJobStatus"),
            "failure_reason": job.get("FailureReason"),
            "output_uri": job.get("Transcript", {}).get("TranscriptFileUri"),
            "media_duration_seconds": job.get("MediaFormat"),
        }

    def get_transcription_result(
        self,
        job_name: str,
        document_id: str,
        wait: bool = False,
        max_wait_seconds: int = 600,
    ) -> ExtractionResult | None:
        """
        Get transcription result.
        Returns None if job is still in progress.
        """
        start_time = time.time()

        while True:
            try:
                status = self.get_transcription_status(job_name)
                job_status = status.get("status")

                if job_status == "COMPLETED":
                    return self._download_and_parse_transcript(
                        job_name,
                        document_id,
                        status.get("output_uri"),
                    )
                elif job_status == "FAILED":
                    raise ExtractionError(
                        f"Transcription failed: {status.get('failure_reason')}",
                        document_id=document_id,
                        service="transcribe",
                    )
                elif job_status == "IN_PROGRESS":
                    if not wait:
                        return None
                    if time.time() - start_time > max_wait_seconds:
                        raise ExtractionError(
                            f"Transcription timed out after {max_wait_seconds}s",
                            document_id=document_id,
                            service="transcribe",
                        )
                    time.sleep(10)  # Poll every 10 seconds

            except ClientError as e:
                raise ExtractionError(
                    f"Failed to get transcription status: {e}",
                    document_id=document_id,
                    service="transcribe",
                )

    def _download_and_parse_transcript(
        self,
        job_name: str,
        document_id: str,
        output_uri: str | None,
    ) -> ExtractionResult:
        """Download and parse transcript from S3."""
        if not output_uri:
            raise ExtractionError(
                "No transcript URI available",
                document_id=document_id,
                service="transcribe",
            )

        # Parse S3 URI
        # Format: s3://bucket/key or https://s3.region.amazonaws.com/bucket/key
        if output_uri.startswith("s3://"):
            parts = output_uri[5:].split("/", 1)
            bucket = parts[0]
            key = parts[1] if len(parts) > 1 else ""
        else:
            # HTTPS URL format
            parts = output_uri.split("/")
            bucket = parts[3]
            key = "/".join(parts[4:])

        # Download transcript
        response = self.clients.s3.get_object(Bucket=bucket, Key=key)
        import json

        transcript_data = json.loads(response["Body"].read().decode("utf-8"))

        return self._parse_transcript(document_id, transcript_data)

    def _parse_transcript(
        self,
        document_id: str,
        transcript_data: dict[str, Any],
    ) -> ExtractionResult:
        """Parse Transcribe output JSON."""
        results = transcript_data.get("results", {})

        # Get full transcript text
        transcripts = results.get("transcripts", [])
        full_text = transcripts[0].get("transcript", "") if transcripts else ""

        # Calculate word count and confidence
        items = results.get("items", [])
        word_count = 0
        total_confidence = 0.0

        for item in items:
            if item.get("type") == "pronunciation":
                word_count += 1
                alternatives = item.get("alternatives", [])
                if alternatives:
                    total_confidence += float(alternatives[0].get("confidence", 0))

        avg_confidence = total_confidence / word_count if word_count > 0 else 0

        # Extract speaker segments if available
        speaker_labels = results.get("speaker_labels", {})
        segments = speaker_labels.get("segments", [])

        return ExtractionResult(
            document_id=document_id,
            extracted_text=full_text,
            confidence=avg_confidence,
            words=word_count,
            raw_response={
                "speaker_count": speaker_labels.get("speakers", 0),
                "segment_count": len(segments),
            },
        )

    def _detect_media_format(self, key: str) -> str:
        """Detect media format from file extension."""
        ext = key.lower().split(".")[-1] if "." in key else ""

        format_map = {
            "mp3": "mp3",
            "mp4": "mp4",
            "wav": "wav",
            "flac": "flac",
            "ogg": "ogg",
            "webm": "webm",
            "m4a": "mp4",
            "amr": "amr",
        }

        return format_map.get(ext, "mp3")

    def delete_transcription_job(self, job_name: str) -> None:
        """Delete a completed transcription job."""
        try:
            self.clients.transcribe.delete_transcription_job(
                TranscriptionJobName=job_name
            )
            logger.info("Deleted transcription job", job_name=job_name)
        except ClientError as e:
            logger.warning(f"Failed to delete transcription job: {e}")
