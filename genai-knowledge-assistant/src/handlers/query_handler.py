"""Query handler for direct Lambda invocation or SQS processing."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.exceptions import QueryError, ValidationError
from src.common.models import ApiResponse, QueryRequest
from src.services.query_service import QueryService

logger = Logger()
tracer = Tracer()
metrics = Metrics()
processor = BatchProcessor(event_type=EventType.SQS)

settings = get_settings()
query_service = QueryService()


@tracer.capture_method
def process_query_record(record: SQSRecord) -> dict[str, Any]:
    """Process a single query from SQS."""
    body = json.loads(record.body)

    # Handle SNS-wrapped messages
    if "Message" in body:
        body = json.loads(body["Message"])

    request = QueryRequest(**body)

    logger.info(
        "Processing query from SQS",
        query_length=len(request.query),
        message_id=record.message_id,
    )

    response = query_service.query(request)

    metrics.add_metric(name="QueriesProcessed", unit="Count", value=1)
    metrics.add_metric(name="TokensUsed", unit="Count", value=response.tokens_used)
    metrics.add_metric(name="LatencyMs", unit="Milliseconds", value=response.latency_ms)

    return response.model_dump(by_alias=True)


@tracer.capture_method
def process_direct_invocation(event: dict[str, Any]) -> dict[str, Any]:
    """Process a direct Lambda invocation for query."""
    try:
        request = QueryRequest(**event)

        logger.info("Processing direct query invocation", query_length=len(request.query))

        response = query_service.query(request)

        metrics.add_metric(name="DirectQueriesProcessed", unit="Count", value=1)

        return ApiResponse(
            success=True,
            data=response.model_dump(by_alias=True),
        ).model_dump(by_alias=True)

    except ValidationError as e:
        logger.warning("Validation error", error=e.message)
        return ApiResponse(
            success=False,
            error=e.message,
            error_code=e.error_code,
        ).model_dump(by_alias=True)

    except QueryError as e:
        logger.error("Query error", error=e.message)
        return ApiResponse(
            success=False,
            error=e.message,
            error_code=e.error_code,
        ).model_dump(by_alias=True)

    except Exception as e:
        logger.exception("Unexpected error processing query")
        return ApiResponse(
            success=False,
            error=str(e),
            error_code="INTERNAL_ERROR",
        ).model_dump(by_alias=True)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for query processing.

    Supports:
    - SQS batch processing
    - Direct Lambda invocation
    """
    # Check if this is an SQS event
    if "Records" in event:
        logger.info("Processing SQS batch", record_count=len(event["Records"]))
        return process_partial_response(
            event=event,
            record_handler=process_query_record,
            processor=processor,
            context=context,
        )

    # Direct invocation
    return process_direct_invocation(event)
