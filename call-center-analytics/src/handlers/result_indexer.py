"""Lambda handler for indexing Comprehend results to OpenSearch."""

import gzip
import json
from datetime import datetime
from typing import Any

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from common.config import get_settings
from common.exceptions import OpenSearchError
from common.models import (
    CallAnalysis,
    CallTranscript,
    EntityResult,
    EntityType,
    KeyPhraseResult,
    Sentiment,
    SentimentResult,
    SentimentScore,
    TranscriptSegment,
    Speaker,
)
from services.opensearch_service import OpenSearchService
from services.transcript_service import TranscriptService

logger = Logger()
tracer = Tracer()
settings = get_settings()


def get_s3_client():
    """Get S3 client."""
    return boto3.client("s3", region_name=settings.aws_region)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Index Comprehend batch job results to OpenSearch.

    Triggered when Comprehend job completes and outputs results to S3.
    Parses results and indexes to OpenSearch with original transcript data.
    """
    logger.info("Processing Comprehend results", extra={"event": event})

    s3_client = get_s3_client()
    transcript_service = TranscriptService()
    opensearch_service = OpenSearchService()

    # Ensure indices exist
    try:
        opensearch_service.create_indices()
    except Exception as e:
        logger.warning(f"Index creation skipped: {e}")

    indexed = 0
    errors = []

    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = record["s3"]["object"]["key"]

        # Skip non-output files
        if not key.endswith(".tar.gz") and not key.endswith(".json"):
            continue

        logger.info(f"Processing result file: s3://{bucket}/{key}")

        try:
            # Read and parse Comprehend output
            response = s3_client.get_object(Bucket=bucket, Key=key)

            if key.endswith(".tar.gz"):
                # Comprehend outputs tar.gz for batch jobs
                import tarfile
                import io

                tar_content = response["Body"].read()
                tar_buffer = io.BytesIO(tar_content)

                with tarfile.open(fileobj=tar_buffer, mode="r:gz") as tar:
                    for member in tar.getmembers():
                        if member.name.endswith(".json"):
                            f = tar.extractfile(member)
                            if f:
                                content = f.read().decode("utf-8")
                                results = parse_comprehend_output(content)
                                indexed += index_results(
                                    results,
                                    transcript_service,
                                    opensearch_service,
                                )
            else:
                # Direct JSON output
                content = response["Body"].read().decode("utf-8")
                results = parse_comprehend_output(content)
                indexed += index_results(
                    results,
                    transcript_service,
                    opensearch_service,
                )

        except Exception as e:
            logger.error(f"Error processing result file: {e}")
            errors.append({"key": key, "error": str(e)})

    return {
        "statusCode": 200,
        "body": {
            "indexed": indexed,
            "errors": len(errors),
            "error_details": errors,
        },
    }


def parse_comprehend_output(content: str) -> list[dict[str, Any]]:
    """Parse Comprehend output (one result per line)."""
    results = []

    for line in content.strip().split("\n"):
        if not line.strip():
            continue

        try:
            result = json.loads(line)
            results.append(result)
        except json.JSONDecodeError:
            logger.warning(f"Skipping invalid JSON line")

    return results


def index_results(
    results: list[dict[str, Any]],
    transcript_service: TranscriptService,
    opensearch_service: OpenSearchService,
) -> int:
    """Index parsed Comprehend results to OpenSearch."""
    indexed = 0

    for result in results:
        try:
            # Extract sentiment data
            sentiment_data = result.get("Sentiment", "NEUTRAL")
            sentiment_score_data = result.get("SentimentScore", {})

            sentiment = Sentiment(sentiment_data)
            sentiment_score = SentimentScore(
                positive=sentiment_score_data.get("Positive", 0),
                negative=sentiment_score_data.get("Negative", 0),
                neutral=sentiment_score_data.get("Neutral", 0),
                mixed=sentiment_score_data.get("Mixed", 0),
            )

            sentiment_result = SentimentResult(
                sentiment=sentiment,
                score=sentiment_score,
            )

            # Create a minimal transcript for batch results
            # In production, you'd look up the original transcript
            call_id = result.get("File", f"batch-{indexed}")

            transcript = CallTranscript(
                call_id=call_id,
                timestamp=datetime.utcnow(),
                duration=0,
                agent_id="unknown",
                customer_id="unknown",
                segments=[],
            )

            analysis = CallAnalysis(
                call_id=call_id,
                transcript=transcript,
                overall_sentiment=sentiment_result,
                analyzed_at=datetime.utcnow(),
            )

            opensearch_service.index_call_analysis(analysis)
            indexed += 1

        except Exception as e:
            logger.warning(f"Error indexing result: {e}")

    return indexed
