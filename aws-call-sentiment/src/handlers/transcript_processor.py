"""Lambda handler for processing transcripts from S3."""

from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from common.config import get_settings
from common.exceptions import TranscriptParseError
from common.models import CallAnalysis
from services.comprehend_service import ComprehendService
from services.opensearch_service import OpenSearchService
from services.transcript_service import TranscriptService

logger = Logger()
tracer = Tracer()
settings = get_settings()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Process transcript files uploaded to S3.

    Triggered by S3 event when new transcript files are uploaded.
    Parses the transcript, analyzes sentiment, and indexes to OpenSearch.
    """
    logger.info("Processing S3 event", extra={"event": event})

    transcript_service = TranscriptService()
    comprehend_service = ComprehendService()
    opensearch_service = OpenSearchService()

    # Ensure indices exist
    try:
        opensearch_service.create_indices()
    except Exception as e:
        logger.warning(f"Index creation skipped: {e}")

    processed = 0
    errors = []

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        logger.info(f"Processing transcript: s3://{bucket}/{key}")

        try:
            # Parse transcript from S3
            transcript = transcript_service.parse_transcript_from_s3(bucket, key)

            # Validate transcript
            validation_errors = transcript_service.validate_transcript(transcript)
            if validation_errors:
                logger.warning(
                    f"Transcript validation warnings: {validation_errors}",
                    extra={"call_id": transcript.call_id},
                )

            # Analyze with Comprehend
            analysis_result = comprehend_service.analyze_transcript(transcript)

            # Create analysis object
            call_analysis = CallAnalysis(
                call_id=transcript.call_id,
                transcript=transcript,
                overall_sentiment=analysis_result["overall_sentiment"],
                customer_sentiment=analysis_result.get("customer_sentiment"),
                agent_sentiment=analysis_result.get("agent_sentiment"),
                entities=analysis_result.get("entities", []),
                key_phrases=analysis_result.get("key_phrases", []),
                analyzed_at=datetime.utcnow(),
            )

            # Index to OpenSearch
            opensearch_service.index_call_analysis(call_analysis)

            processed += 1
            logger.info(
                f"Successfully processed call {transcript.call_id}",
                extra={
                    "call_id": transcript.call_id,
                    "sentiment": call_analysis.overall_sentiment.sentiment.value,
                },
            )

        except TranscriptParseError as e:
            logger.error(f"Failed to parse transcript: {e.message}")
            errors.append({"key": key, "error": e.message})
        except Exception as e:
            logger.error(f"Error processing transcript: {e}")
            errors.append({"key": key, "error": str(e)})

    return {
        "statusCode": 200,
        "body": {
            "processed": processed,
            "errors": len(errors),
            "error_details": errors,
        },
    }
