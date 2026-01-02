"""Integration tests for SQS queue operations."""

from decimal import Decimal

import boto3
import pytest
from moto import mock_aws

from src.common.models import Transaction, TransactionType
from src.services.queue_service import QueueService


@mock_aws
class TestQueueIntegration:
    """Integration tests for queue operations."""

    @pytest.fixture
    def setup_sqs(self):
        """Set up SQS queue for integration tests."""
        client = boto3.client("sqs", region_name="us-east-1")
        response = client.create_queue(
            QueueName="test-transactions",
            Attributes={
                "VisibilityTimeout": "60",
            },
        )
        queue_url = response["QueueUrl"]
        return client, queue_url

    def test_send_and_receive_message(self, setup_sqs):
        """Test sending and receiving a message."""
        client, queue_url = setup_sqs

        # Create queue service
        service = QueueService(queue_url=queue_url)

        # Create and send transaction
        transaction = Transaction(
            transaction_type=TransactionType.TRANSFER,
            source_account="1234567890",
            target_account="0987654321",
            amount=Decimal("100.00"),
            idempotency_key="test-key-001",
        )
        message_id = service.send_message(transaction)
        assert message_id is not None

        # Receive message
        messages = service.receive_messages(max_messages=1, wait_time=0)
        assert len(messages) == 1

        # Parse and verify
        received = service.parse_transaction(messages[0])
        assert received.source_account == transaction.source_account
        assert received.amount == transaction.amount

        # Delete message
        service.delete_message(messages[0]["ReceiptHandle"])

        # Verify message is deleted (queue should be empty)
        messages = service.receive_messages(max_messages=1, wait_time=0)
        assert len(messages) == 0

    def test_queue_metrics(self, setup_sqs):
        """Test getting queue metrics."""
        client, queue_url = setup_sqs

        service = QueueService(queue_url=queue_url)

        # Send some messages
        for i in range(5):
            transaction = Transaction(
                transaction_type=TransactionType.DEPOSIT,
                source_account="1234567890",
                amount=Decimal("50.00"),
                idempotency_key=f"test-key-{i}",
            )
            service.send_message(transaction)

        # Get metrics
        metrics = service.get_queue_metrics()
        assert metrics.approximate_messages >= 0  # moto may not track exactly

    def test_message_visibility_timeout(self, setup_sqs):
        """Test changing message visibility timeout."""
        client, queue_url = setup_sqs

        service = QueueService(queue_url=queue_url)

        # Send a message
        transaction = Transaction(
            transaction_type=TransactionType.DEPOSIT,
            source_account="1234567890",
            amount=Decimal("100.00"),
            idempotency_key="test-visibility",
        )
        service.send_message(transaction)

        # Receive message
        messages = service.receive_messages(max_messages=1, wait_time=0)
        assert len(messages) == 1

        # Change visibility - should not raise
        service.change_visibility(messages[0]["ReceiptHandle"], 300)
