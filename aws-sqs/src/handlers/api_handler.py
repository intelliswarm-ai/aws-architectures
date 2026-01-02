"""API Gateway Lambda handler for receiving transactions."""

import json
from decimal import Decimal
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.event_handler.exceptions import BadRequestError
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from ..common.config import settings
from ..common.exceptions import ValidationError
from ..common.models import Currency, Transaction, TransactionType
from ..services.queue_service import QueueService

logger = Logger(service=settings.service_name)
tracer = Tracer(service=settings.service_name)
metrics = Metrics(service=settings.service_name, namespace="BankingPlatform")

app = APIGatewayRestResolver()
queue_service = QueueService()


@app.post("/transactions")
@tracer.capture_method
def create_transaction() -> dict[str, Any]:
    """Create a new banking transaction.

    Request body:
        {
            "transaction_type": "TRANSFER",
            "source_account": "1234567890",
            "target_account": "0987654321",
            "amount": 100.00,
            "currency": "USD",
            "description": "Payment for services",
            "idempotency_key": "unique-key-123"
        }

    Returns:
        Transaction details with message ID.
    """
    try:
        body = app.current_event.json_body
        if not body:
            raise BadRequestError("Request body is required")

        # Parse and validate transaction
        transaction = Transaction(
            transaction_type=TransactionType(body.get("transaction_type")),
            source_account=body.get("source_account"),
            target_account=body.get("target_account"),
            amount=Decimal(str(body.get("amount", 0))),
            currency=Currency(body.get("currency", "USD")),
            description=body.get("description"),
            idempotency_key=body.get("idempotency_key"),
        )

        # Send to queue
        message_id = queue_service.send_message(transaction)

        # Record metrics
        metrics.add_metric(
            name="TransactionsReceived",
            unit=MetricUnit.Count,
            value=1,
        )
        metrics.add_metric(
            name="TransactionAmount",
            unit=MetricUnit.Count,
            value=float(transaction.amount),
        )

        logger.info(
            "Transaction queued successfully",
            extra={
                "transaction_id": transaction.transaction_id,
                "message_id": message_id,
                "type": transaction.transaction_type.value,
            },
        )

        return {
            "statusCode": 202,
            "body": {
                "message": "Transaction accepted for processing",
                "transaction_id": transaction.transaction_id,
                "message_id": message_id,
                "status": "QUEUED",
            },
        }

    except (ValueError, TypeError) as e:
        logger.warning("Invalid request", extra={"error": str(e)})
        metrics.add_metric(
            name="ValidationErrors",
            unit=MetricUnit.Count,
            value=1,
        )
        raise BadRequestError(f"Invalid request: {e}") from e


@app.get("/transactions/<transaction_id>")
@tracer.capture_method
def get_transaction(transaction_id: str) -> dict[str, Any]:
    """Get transaction status by ID.

    Args:
        transaction_id: Transaction ID to look up.

    Returns:
        Transaction details if found.
    """
    from ..services.transaction_service import TransactionService

    service = TransactionService()
    result = service.get_transaction(transaction_id)

    if not result:
        return {
            "statusCode": 404,
            "body": {"error": "Transaction not found"},
        }

    # Convert DynamoDB item to response
    return {
        "statusCode": 200,
        "body": {
            "transaction_id": result.get("transaction_id", {}).get("S"),
            "transaction_type": result.get("transaction_type", {}).get("S"),
            "source_account": result.get("source_account", {}).get("S"),
            "target_account": result.get("target_account", {}).get("S"),
            "amount": result.get("amount", {}).get("N"),
            "currency": result.get("currency", {}).get("S"),
            "status": result.get("status", {}).get("S"),
            "processed_at": result.get("processed_at", {}).get("S"),
            "processor_id": result.get("processor_id", {}).get("S"),
        },
    }


@app.get("/health")
def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {
        "statusCode": 200,
        "body": {"status": "healthy", "service": settings.service_name},
    }


@app.get("/metrics")
@tracer.capture_method
def get_queue_metrics() -> dict[str, Any]:
    """Get current queue metrics."""
    queue_metrics = queue_service.get_queue_metrics()
    return {
        "statusCode": 200,
        "body": {
            "queue_url": queue_metrics.queue_url,
            "approximate_messages": queue_metrics.approximate_messages,
            "approximate_messages_not_visible": (
                queue_metrics.approximate_messages_not_visible
            ),
            "total_messages": queue_metrics.total_messages,
            "timestamp": queue_metrics.timestamp.isoformat(),
        },
    }


@logger.inject_lambda_context(
    correlation_id_path=correlation_paths.API_GATEWAY_REST,
)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda handler for API Gateway events."""
    return app.resolve(event, context)
