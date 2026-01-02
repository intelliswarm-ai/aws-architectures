"""Unit tests for QueueService."""

import json
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.common.models import Transaction, TransactionType
from src.services.queue_service import QueueService


class TestQueueService:
    """Tests for QueueService."""

    @pytest.fixture
    def mock_sqs_client(self):
        """Create a mock SQS client."""
        return MagicMock()

    @pytest.fixture
    def queue_service(self, mock_sqs_client):
        """Create a QueueService with mocked client."""
        with patch("src.services.queue_service.get_sqs_client", return_value=mock_sqs_client):
            service = QueueService(queue_url="https://sqs.test.com/test-queue")
            service.client = mock_sqs_client
            return service

    def test_send_message(self, queue_service, sample_transaction_data):
        """Test sending a message to the queue."""
        queue_service.client.send_message.return_value = {"MessageId": "test-msg-id"}

        transaction = Transaction(**sample_transaction_data)
        message_id = queue_service.send_message(transaction)

        assert message_id == "test-msg-id"
        queue_service.client.send_message.assert_called_once()

        call_args = queue_service.client.send_message.call_args
        assert call_args.kwargs["QueueUrl"] == "https://sqs.test.com/test-queue"
        assert "MessageBody" in call_args.kwargs

    def test_receive_messages(self, queue_service, sample_sqs_message):
        """Test receiving messages from the queue."""
        queue_service.client.receive_message.return_value = {
            "Messages": [sample_sqs_message]
        }

        messages = queue_service.receive_messages(max_messages=1)

        assert len(messages) == 1
        assert messages[0]["MessageId"] == "test-message-id"

    def test_receive_messages_empty_queue(self, queue_service):
        """Test receiving from an empty queue."""
        queue_service.client.receive_message.return_value = {}

        messages = queue_service.receive_messages()

        assert messages == []

    def test_delete_message(self, queue_service):
        """Test deleting a message from the queue."""
        queue_service.delete_message("test-receipt-handle")

        queue_service.client.delete_message.assert_called_once_with(
            QueueUrl="https://sqs.test.com/test-queue",
            ReceiptHandle="test-receipt-handle",
        )

    def test_get_queue_metrics(self, queue_service):
        """Test getting queue metrics."""
        queue_service.client.get_queue_attributes.return_value = {
            "Attributes": {
                "ApproximateNumberOfMessages": "100",
                "ApproximateNumberOfMessagesNotVisible": "25",
                "ApproximateNumberOfMessagesDelayed": "10",
            }
        }

        metrics = queue_service.get_queue_metrics()

        assert metrics.approximate_messages == 100
        assert metrics.approximate_messages_not_visible == 25
        assert metrics.approximate_messages_delayed == 10
        assert metrics.total_messages == 135

    def test_parse_transaction(self, queue_service, sample_sqs_message):
        """Test parsing a transaction from an SQS message."""
        transaction = queue_service.parse_transaction(sample_sqs_message)

        assert transaction.transaction_id == "test-txn-id"
        assert transaction.transaction_type == TransactionType.TRANSFER
        assert transaction.source_account == "1234567890"
        assert transaction.amount == Decimal("100.00")

    def test_change_visibility(self, queue_service):
        """Test changing message visibility timeout."""
        queue_service.change_visibility("test-receipt-handle", 120)

        queue_service.client.change_message_visibility.assert_called_once_with(
            QueueUrl="https://sqs.test.com/test-queue",
            ReceiptHandle="test-receipt-handle",
            VisibilityTimeout=120,
        )
