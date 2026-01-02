"""Idempotency service for duplicate transaction detection."""

import time
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger

from ..common.clients import get_dynamodb_client
from ..common.config import settings
from ..common.exceptions import DuplicateTransactionError

logger = Logger(service=settings.service_name)

# TTL for idempotency records (24 hours)
IDEMPOTENCY_TTL_SECONDS = 86400


class IdempotencyService:
    """Service for managing transaction idempotency."""

    def __init__(self, table_name: str | None = None) -> None:
        """Initialize idempotency service."""
        self.table_name = table_name or settings.idempotency_table_name
        self.client = get_dynamodb_client()

    def check_and_set(self, idempotency_key: str, transaction_id: str) -> bool:
        """Check if a transaction is duplicate and set if not.

        Uses DynamoDB conditional writes for atomic check-and-set.

        Args:
            idempotency_key: Unique idempotency key.
            transaction_id: Associated transaction ID.

        Returns:
            True if this is a new transaction, False if duplicate.

        Raises:
            DuplicateTransactionError: If transaction was already processed.
        """
        ttl = int(time.time()) + IDEMPOTENCY_TTL_SECONDS

        try:
            self.client.put_item(
                TableName=self.table_name,
                Item={
                    "idempotency_key": {"S": idempotency_key},
                    "transaction_id": {"S": transaction_id},
                    "created_at": {"S": datetime.utcnow().isoformat()},
                    "ttl": {"N": str(ttl)},
                },
                ConditionExpression="attribute_not_exists(idempotency_key)",
            )
            logger.debug(
                "Idempotency key registered",
                extra={
                    "idempotency_key": idempotency_key,
                    "transaction_id": transaction_id,
                },
            )
            return True
        except self.client.exceptions.ConditionalCheckFailedException:
            logger.warning(
                "Duplicate transaction detected",
                extra={"idempotency_key": idempotency_key},
            )
            raise DuplicateTransactionError(idempotency_key)
        except Exception as e:
            logger.error(
                "Failed to check idempotency",
                extra={
                    "error": str(e),
                    "idempotency_key": idempotency_key,
                },
            )
            raise

    def get_existing(self, idempotency_key: str) -> dict[str, Any] | None:
        """Get existing idempotency record.

        Args:
            idempotency_key: Unique idempotency key.

        Returns:
            Existing record if found, None otherwise.
        """
        try:
            response = self.client.get_item(
                TableName=self.table_name,
                Key={"idempotency_key": {"S": idempotency_key}},
            )
            item = response.get("Item")
            if item:
                return {
                    "idempotency_key": item["idempotency_key"]["S"],
                    "transaction_id": item["transaction_id"]["S"],
                    "created_at": item["created_at"]["S"],
                }
            return None
        except Exception as e:
            logger.error(
                "Failed to get idempotency record",
                extra={
                    "error": str(e),
                    "idempotency_key": idempotency_key,
                },
            )
            raise

    def remove(self, idempotency_key: str) -> None:
        """Remove an idempotency record.

        Useful for cleanup or allowing retry of failed transactions.

        Args:
            idempotency_key: Unique idempotency key to remove.
        """
        try:
            self.client.delete_item(
                TableName=self.table_name,
                Key={"idempotency_key": {"S": idempotency_key}},
            )
            logger.debug(
                "Idempotency record removed",
                extra={"idempotency_key": idempotency_key},
            )
        except Exception as e:
            logger.error(
                "Failed to remove idempotency record",
                extra={
                    "error": str(e),
                    "idempotency_key": idempotency_key,
                },
            )
            raise
