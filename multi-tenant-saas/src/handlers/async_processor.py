"""SQS Batch Processor with Partial Failure Support.

This handler processes SQS messages in batches, supporting partial batch
failures for reliable message processing.
"""

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

from src.common.config import get_settings
from src.common.exceptions import NonRetryableError, RetryableError
from src.common.utils import json_loads

logger = Logger()
tracer = Tracer()
metrics = Metrics()
processor = BatchProcessor(event_type=EventType.SQS)

settings = get_settings()


@tracer.capture_method
def process_record(record: SQSRecord) -> dict[str, Any]:
    """Process a single SQS record.

    Args:
        record: SQS record to process

    Returns:
        Processing result

    Raises:
        RetryableError: For transient failures (message returns to queue)
        NonRetryableError: For permanent failures (message goes to DLQ)
    """
    message_id = record.message_id
    logger.info(f"Processing message {message_id}")

    try:
        # Parse message body
        body = json_loads(record.body)
        message_type = body.get("type", "unknown")
        payload = body.get("payload", {})

        logger.info(
            f"Message type: {message_type}",
            extra={"message_id": message_id, "type": message_type},
        )

        # Route to appropriate handler based on message type
        result = route_message(message_type, payload, record)

        metrics.add_metric(name="MessagesProcessed", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="MessageType", value=message_type)

        return {
            "message_id": message_id,
            "type": message_type,
            "status": "success",
            "result": result,
        }

    except NonRetryableError as e:
        # Permanent failure - message will go to DLQ
        logger.error(f"Non-retryable error for message {message_id}: {e.message}")
        metrics.add_metric(name="MessagesFailedPermanent", unit=MetricUnit.Count, value=1)
        raise

    except RetryableError as e:
        # Transient failure - message returns to queue for retry
        logger.warning(f"Retryable error for message {message_id}: {e.message}")
        metrics.add_metric(name="MessagesFailedRetry", unit=MetricUnit.Count, value=1)
        raise

    except Exception as e:
        # Unknown error - treat as retryable
        logger.exception(f"Unexpected error for message {message_id}: {e}")
        metrics.add_metric(name="MessagesFailedUnknown", unit=MetricUnit.Count, value=1)
        raise RetryableError(f"Unexpected error: {e}")


@tracer.capture_method
def route_message(
    message_type: str,
    payload: dict[str, Any],
    record: SQSRecord,
) -> Any:
    """Route message to appropriate handler based on type.

    Args:
        message_type: Type of message
        payload: Message payload
        record: Original SQS record

    Returns:
        Handler result
    """
    handlers = {
        "tenant.created": handle_tenant_created,
        "tenant.updated": handle_tenant_updated,
        "tenant.deleted": handle_tenant_deleted,
        "resource.process": handle_resource_process,
        "notification.send": handle_notification,
        "audit.log": handle_audit_log,
    }

    handler_func = handlers.get(message_type)
    if not handler_func:
        logger.warning(f"Unknown message type: {message_type}")
        # Don't retry unknown message types
        raise NonRetryableError(f"Unknown message type: {message_type}")

    return handler_func(payload, record)


def handle_tenant_created(payload: dict[str, Any], record: SQSRecord) -> dict[str, Any]:
    """Handle tenant creation events."""
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise NonRetryableError("Missing tenant_id in payload")

    logger.info(f"Processing tenant creation: {tenant_id}")

    # TODO: Implement tenant setup logic
    # - Create tenant-specific resources
    # - Initialize default settings
    # - Send welcome notification

    return {"tenant_id": tenant_id, "action": "created"}


def handle_tenant_updated(payload: dict[str, Any], record: SQSRecord) -> dict[str, Any]:
    """Handle tenant update events."""
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise NonRetryableError("Missing tenant_id in payload")

    logger.info(f"Processing tenant update: {tenant_id}")

    # TODO: Implement tenant update logic
    # - Update cached tenant data
    # - Propagate changes to dependent services

    return {"tenant_id": tenant_id, "action": "updated"}


def handle_tenant_deleted(payload: dict[str, Any], record: SQSRecord) -> dict[str, Any]:
    """Handle tenant deletion events."""
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        raise NonRetryableError("Missing tenant_id in payload")

    logger.info(f"Processing tenant deletion: {tenant_id}")

    # TODO: Implement tenant cleanup logic
    # - Archive tenant data
    # - Clean up resources
    # - Notify relevant parties

    return {"tenant_id": tenant_id, "action": "deleted"}


def handle_resource_process(payload: dict[str, Any], record: SQSRecord) -> dict[str, Any]:
    """Handle resource processing requests."""
    resource_id = payload.get("resource_id")
    tenant_id = payload.get("tenant_id")

    if not resource_id or not tenant_id:
        raise NonRetryableError("Missing resource_id or tenant_id in payload")

    logger.info(f"Processing resource {resource_id} for tenant {tenant_id}")

    # TODO: Implement resource processing logic

    return {"resource_id": resource_id, "tenant_id": tenant_id, "action": "processed"}


def handle_notification(payload: dict[str, Any], record: SQSRecord) -> dict[str, Any]:
    """Handle notification sending."""
    notification_type = payload.get("type")
    recipient = payload.get("recipient")

    if not notification_type or not recipient:
        raise NonRetryableError("Missing notification type or recipient")

    logger.info(f"Sending {notification_type} notification to {recipient}")

    # TODO: Implement notification sending
    # - Route to appropriate channel (email, SMS, push)
    # - Track delivery status

    return {"type": notification_type, "recipient": recipient, "status": "sent"}


def handle_audit_log(payload: dict[str, Any], record: SQSRecord) -> dict[str, Any]:
    """Handle audit log events."""
    event_type = payload.get("event_type")
    tenant_id = payload.get("tenant_id")

    logger.info(f"Logging audit event: {event_type} for tenant {tenant_id}")

    # TODO: Implement audit log persistence
    # - Write to audit DynamoDB table
    # - Forward to SIEM if configured

    return {"event_type": event_type, "status": "logged"}


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """SQS batch handler with partial failure support.

    Args:
        event: SQS event with batch of records
        context: Lambda context

    Returns:
        Batch response with failed message IDs
    """
    records = event.get("Records", [])
    logger.info(f"Processing batch of {len(records)} messages")

    return process_partial_response(
        event=event,
        record_handler=process_record,
        processor=processor,
        context=context,
    )
