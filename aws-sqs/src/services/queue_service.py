"""SQS queue service for message operations."""

import json
from typing import Any

from aws_lambda_powertools import Logger

from ..common.clients import get_sqs_client
from ..common.config import settings
from ..common.exceptions import QueueError
from ..common.models import QueueMetrics, Transaction

logger = Logger(service=settings.service_name)


class QueueService:
    """Service for SQS queue operations."""

    def __init__(self, queue_url: str | None = None) -> None:
        """Initialize queue service."""
        self.queue_url = queue_url or settings.transaction_queue_url
        self.client = get_sqs_client()

    def send_message(self, transaction: Transaction) -> str:
        """Send a transaction message to the queue.

        Args:
            transaction: Transaction to send.

        Returns:
            Message ID from SQS.

        Raises:
            QueueError: If sending fails.
        """
        try:
            response = self.client.send_message(
                QueueUrl=self.queue_url,
                MessageBody=transaction.model_dump_json(),
                MessageAttributes={
                    "TransactionType": {
                        "DataType": "String",
                        "StringValue": transaction.transaction_type.value,
                    },
                    "Currency": {
                        "DataType": "String",
                        "StringValue": transaction.currency.value,
                    },
                    "SourceAccount": {
                        "DataType": "String",
                        "StringValue": transaction.source_account,
                    },
                },
            )
            message_id = response["MessageId"]
            logger.info(
                "Message sent to queue",
                extra={
                    "message_id": message_id,
                    "transaction_id": transaction.transaction_id,
                },
            )
            return message_id
        except Exception as e:
            logger.error(
                "Failed to send message",
                extra={
                    "error": str(e),
                    "transaction_id": transaction.transaction_id,
                },
            )
            raise QueueError(f"Failed to send message: {e}", self.queue_url) from e

    def receive_messages(
        self,
        max_messages: int | None = None,
        wait_time: int | None = None,
    ) -> list[dict[str, Any]]:
        """Receive messages from the queue.

        Args:
            max_messages: Maximum number of messages to receive (1-10).
            wait_time: Long polling wait time in seconds.

        Returns:
            List of SQS message dictionaries.

        Raises:
            QueueError: If receiving fails.
        """
        try:
            response = self.client.receive_message(
                QueueUrl=self.queue_url,
                MaxNumberOfMessages=max_messages or settings.max_number_of_messages,
                WaitTimeSeconds=wait_time or settings.wait_time_seconds,
                VisibilityTimeout=settings.visibility_timeout,
                MessageAttributeNames=["All"],
                AttributeNames=["All"],
            )
            messages = response.get("Messages", [])
            logger.debug(
                "Received messages",
                extra={"message_count": len(messages)},
            )
            return messages
        except Exception as e:
            logger.error("Failed to receive messages", extra={"error": str(e)})
            raise QueueError(f"Failed to receive messages: {e}", self.queue_url) from e

    def delete_message(self, receipt_handle: str) -> None:
        """Delete a message from the queue.

        Args:
            receipt_handle: Receipt handle of the message to delete.

        Raises:
            QueueError: If deletion fails.
        """
        try:
            self.client.delete_message(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
            )
            logger.debug(
                "Message deleted",
                extra={"receipt_handle": receipt_handle[:50]},
            )
        except Exception as e:
            logger.error("Failed to delete message", extra={"error": str(e)})
            raise QueueError(f"Failed to delete message: {e}", self.queue_url) from e

    def change_visibility(
        self,
        receipt_handle: str,
        visibility_timeout: int,
    ) -> None:
        """Change message visibility timeout.

        Args:
            receipt_handle: Receipt handle of the message.
            visibility_timeout: New visibility timeout in seconds.

        Raises:
            QueueError: If operation fails.
        """
        try:
            self.client.change_message_visibility(
                QueueUrl=self.queue_url,
                ReceiptHandle=receipt_handle,
                VisibilityTimeout=visibility_timeout,
            )
        except Exception as e:
            logger.error(
                "Failed to change visibility",
                extra={"error": str(e)},
            )
            raise QueueError(
                f"Failed to change visibility: {e}",
                self.queue_url,
            ) from e

    def get_queue_metrics(self) -> QueueMetrics:
        """Get queue metrics for monitoring.

        Returns:
            QueueMetrics with current queue state.

        Raises:
            QueueError: If getting attributes fails.
        """
        try:
            response = self.client.get_queue_attributes(
                QueueUrl=self.queue_url,
                AttributeNames=[
                    "ApproximateNumberOfMessages",
                    "ApproximateNumberOfMessagesNotVisible",
                    "ApproximateNumberOfMessagesDelayed",
                ],
            )
            attrs = response.get("Attributes", {})
            return QueueMetrics(
                queue_url=self.queue_url,
                approximate_messages=int(
                    attrs.get("ApproximateNumberOfMessages", 0)
                ),
                approximate_messages_not_visible=int(
                    attrs.get("ApproximateNumberOfMessagesNotVisible", 0)
                ),
                approximate_messages_delayed=int(
                    attrs.get("ApproximateNumberOfMessagesDelayed", 0)
                ),
            )
        except Exception as e:
            logger.error("Failed to get queue metrics", extra={"error": str(e)})
            raise QueueError(
                f"Failed to get queue metrics: {e}",
                self.queue_url,
            ) from e

    def parse_transaction(self, message: dict[str, Any]) -> Transaction:
        """Parse a transaction from an SQS message.

        Args:
            message: SQS message dictionary.

        Returns:
            Parsed Transaction object.

        Raises:
            ValidationError: If parsing fails.
        """
        body = message.get("Body", "{}")
        data = json.loads(body)
        return Transaction.model_validate(data)

    def purge_queue(self) -> None:
        """Purge all messages from the queue.

        Warning: This is a destructive operation.

        Raises:
            QueueError: If purge fails.
        """
        try:
            self.client.purge_queue(QueueUrl=self.queue_url)
            logger.warning("Queue purged", extra={"queue_url": self.queue_url})
        except Exception as e:
            logger.error("Failed to purge queue", extra={"error": str(e)})
            raise QueueError(f"Failed to purge queue: {e}", self.queue_url) from e
