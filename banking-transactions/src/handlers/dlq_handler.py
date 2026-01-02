"""Dead Letter Queue handler for failed messages."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

from ..common.clients import get_dynamodb_client
from ..common.config import settings

logger = Logger(service=settings.service_name)
tracer = Tracer(service=settings.service_name)
metrics = Metrics(service=settings.service_name, namespace="BankingPlatform")

processor = BatchProcessor(event_type=EventType.SQS)

DLQ_TABLE_NAME = "banking-dlq-records"


@tracer.capture_method
def record_handler(record: SQSRecord) -> None:
    """Process a single DLQ message.

    Failed messages are stored in DynamoDB for investigation.

    Args:
        record: SQS record from the DLQ.
    """
    message_id = record.message_id
    body = record.body
    attributes = record.attributes

    logger.warning(
        "Processing DLQ message",
        extra={
            "message_id": message_id,
            "approximate_receive_count": attributes.get(
                "ApproximateReceiveCount"
            ),
        },
    )

    # Parse the original transaction
    try:
        transaction_data = json.loads(body)
    except json.JSONDecodeError:
        transaction_data = {"raw_body": body}

    # Store in DLQ records table
    client = get_dynamodb_client()
    try:
        client.put_item(
            TableName=DLQ_TABLE_NAME,
            Item={
                "message_id": {"S": message_id},
                "transaction_id": {
                    "S": transaction_data.get("transaction_id", "unknown")
                },
                "original_body": {"S": body},
                "receive_count": {
                    "N": str(attributes.get("ApproximateReceiveCount", 0))
                },
                "first_received": {
                    "S": attributes.get(
                        "ApproximateFirstReceiveTimestamp", ""
                    )
                },
                "sent_timestamp": {
                    "S": attributes.get("SentTimestamp", "")
                },
                "error_source": {"S": "DLQ"},
                "status": {"S": "PENDING_INVESTIGATION"},
            },
        )
        logger.info(
            "DLQ record stored",
            extra={"message_id": message_id},
        )
    except Exception as e:
        logger.error(
            "Failed to store DLQ record",
            extra={"message_id": message_id, "error": str(e)},
        )
        raise

    # Record metrics
    metrics.add_metric(
        name="DLQMessagesProcessed",
        unit=MetricUnit.Count,
        value=1,
    )

    # Add dimension for transaction type if available
    transaction_type = transaction_data.get("transaction_type", "UNKNOWN")
    metrics.add_dimension(name="TransactionType", value=transaction_type)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda handler for DLQ processing.

    Uses batch processing with partial failure support.

    Args:
        event: SQS event with DLQ messages.
        context: Lambda context.

    Returns:
        Batch processing response with item failures.
    """
    return process_partial_response(
        event=event,
        record_handler=record_handler,
        processor=processor,
        context=context,
    )
