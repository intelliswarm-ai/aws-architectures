"""Lambda handler for managing Comprehend batch jobs."""

import uuid
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from common.config import get_settings
from common.exceptions import ComprehendError
from services.comprehend_service import ComprehendService
from services.transcript_service import TranscriptService

logger = Logger()
tracer = Tracer()
settings = get_settings()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def start_batch_job_handler(
    event: dict[str, Any],
    context: LambdaContext,
) -> dict[str, Any]:
    """Start a Comprehend batch sentiment analysis job.

    Event format:
    {
        "action": "start_sentiment" | "start_entities",
        "input_prefix": "input/batch-001/",
        "language": "en"
    }
    """
    logger.info("Starting Comprehend batch job", extra={"event": event})

    action = event.get("action", "start_sentiment")
    input_prefix = event.get("input_prefix", settings.transcripts_prefix)
    language = event.get("language", settings.default_language)

    transcript_service = TranscriptService()
    comprehend_service = ComprehendService()

    # List transcripts to process
    transcript_keys = transcript_service.list_transcripts(
        bucket=settings.transcripts_bucket,
        prefix=input_prefix,
    )

    if not transcript_keys:
        logger.warning("No transcripts found to process")
        return {
            "statusCode": 200,
            "body": {"message": "No transcripts found", "job_id": None},
        }

    # Load and prepare transcripts
    transcripts = []
    for key in transcript_keys:
        try:
            transcript = transcript_service.parse_transcript_from_s3(
                bucket=settings.transcripts_bucket,
                key=key,
            )
            transcripts.append(transcript)
        except Exception as e:
            logger.warning(f"Skipping invalid transcript {key}: {e}")

    if not transcripts:
        logger.warning("No valid transcripts to process")
        return {
            "statusCode": 200,
            "body": {"message": "No valid transcripts", "job_id": None},
        }

    # Upload prepared input for Comprehend
    batch_id = uuid.uuid4().hex[:8]
    input_key = f"{settings.output_prefix}batch-{batch_id}/input.txt"
    input_s3_uri = transcript_service.upload_for_comprehend(
        transcripts=transcripts,
        bucket=settings.output_bucket,
        key=input_key,
    )

    output_s3_uri = f"s3://{settings.output_bucket}/{settings.output_prefix}batch-{batch_id}/output/"

    # Start the appropriate job type
    try:
        if action == "start_entities":
            job_status = comprehend_service.start_entities_batch_job(
                input_s3_uri=input_s3_uri,
                output_s3_uri=output_s3_uri,
                language=language,
            )
        else:
            job_status = comprehend_service.start_sentiment_batch_job(
                input_s3_uri=input_s3_uri,
                output_s3_uri=output_s3_uri,
                language=language,
            )

        logger.info(
            f"Started batch job {job_status.job_id}",
            extra={
                "job_id": job_status.job_id,
                "job_type": action,
                "transcript_count": len(transcripts),
            },
        )

        return {
            "statusCode": 200,
            "body": {
                "job_id": job_status.job_id,
                "job_name": job_status.job_name,
                "status": job_status.status.value,
                "input_s3_uri": job_status.input_s3_uri,
                "output_s3_uri": job_status.output_s3_uri,
                "transcript_count": len(transcripts),
            },
        }

    except ComprehendError as e:
        logger.error(f"Failed to start batch job: {e.message}")
        return {
            "statusCode": 500,
            "body": {"error": e.message},
        }


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def check_job_status_handler(
    event: dict[str, Any],
    context: LambdaContext,
) -> dict[str, Any]:
    """Check status of a Comprehend batch job.

    Event format:
    {
        "job_id": "abc123",
        "job_type": "sentiment" | "entities"
    }
    """
    job_id = event.get("job_id")
    job_type = event.get("job_type", "sentiment")

    if not job_id:
        return {
            "statusCode": 400,
            "body": {"error": "job_id is required"},
        }

    comprehend_service = ComprehendService()

    try:
        job_status = comprehend_service.get_job_status(job_id, job_type)

        return {
            "statusCode": 200,
            "body": {
                "job_id": job_status.job_id,
                "job_name": job_status.job_name,
                "status": job_status.status.value,
                "submit_time": (
                    job_status.submit_time.isoformat()
                    if job_status.submit_time
                    else None
                ),
                "end_time": (
                    job_status.end_time.isoformat() if job_status.end_time else None
                ),
                "output_s3_uri": job_status.output_s3_uri,
                "message": job_status.message,
            },
        }

    except ComprehendError as e:
        logger.error(f"Failed to get job status: {e.message}")
        return {
            "statusCode": 500,
            "body": {"error": e.message},
        }
