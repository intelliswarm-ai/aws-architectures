"""Unit tests for data models."""

from datetime import datetime

import pytest

from common.models import (
    SMSEvent,
    InboundSMS,
    SMSResponse,
    Subscriber,
    SubscriptionStatus,
    AnalyticsMetrics,
)


class TestInboundSMS:
    """Tests for InboundSMS model."""

    def test_get_normalized_response(self):
        """Test response normalization."""
        inbound = InboundSMS(
            event_timestamp=datetime.utcnow(),
            origination_number="+1234567890",
            destination_number="+0987654321",
            message_body="  yes  ",
        )
        assert inbound.get_normalized_response() == "YES"

    def test_is_opt_out_stop(self):
        """Test opt-out detection for STOP."""
        inbound = InboundSMS(
            event_timestamp=datetime.utcnow(),
            origination_number="+1234567890",
            destination_number="+0987654321",
            message_body="STOP",
        )
        assert inbound.is_opt_out() is True
        assert inbound.is_confirmation() is False

    def test_is_opt_out_unsubscribe(self):
        """Test opt-out detection for UNSUBSCRIBE."""
        inbound = InboundSMS(
            event_timestamp=datetime.utcnow(),
            origination_number="+1234567890",
            destination_number="+0987654321",
            message_body="unsubscribe",
        )
        assert inbound.is_opt_out() is True

    def test_is_confirmation_yes(self):
        """Test confirmation detection for YES."""
        inbound = InboundSMS(
            event_timestamp=datetime.utcnow(),
            origination_number="+1234567890",
            destination_number="+0987654321",
            message_body="YES",
        )
        assert inbound.is_confirmation() is True
        assert inbound.is_opt_out() is False

    def test_is_confirmation_y(self):
        """Test confirmation detection for Y."""
        inbound = InboundSMS(
            event_timestamp=datetime.utcnow(),
            origination_number="+1234567890",
            destination_number="+0987654321",
            message_body="y",
        )
        assert inbound.is_confirmation() is True

    def test_regular_message(self):
        """Test regular message is neither opt-out nor confirmation."""
        inbound = InboundSMS(
            event_timestamp=datetime.utcnow(),
            origination_number="+1234567890",
            destination_number="+0987654321",
            message_body="Hello, I have a question",
        )
        assert inbound.is_opt_out() is False
        assert inbound.is_confirmation() is False


class TestSMSResponse:
    """Tests for SMSResponse model."""

    def test_to_dynamodb_item(self):
        """Test conversion to DynamoDB item."""
        response = SMSResponse(
            subscriber_id="sub-123",
            response_timestamp="2024-01-15T10:30:00Z",
            phone_number="+1234567890",
            response_text="YES",
            normalized_response="YES",
            campaign_id="camp-001",
            journey_id="journey-001",
            response_date="2024-01-15",
            sentiment="positive",
            is_opt_out=False,
            is_confirmation=True,
            ttl=1736899200,
        )

        item = response.to_dynamodb_item()

        assert item["subscriber_id"]["S"] == "sub-123"
        assert item["phone_number"]["S"] == "+1234567890"
        assert item["is_confirmation"]["BOOL"] is True
        assert item["is_opt_out"]["BOOL"] is False
        assert item["sentiment"]["S"] == "positive"


class TestSubscriber:
    """Tests for Subscriber model."""

    def test_default_values(self):
        """Test default subscriber values."""
        subscriber = Subscriber(
            subscriber_id="sub-123",
            phone_number="+1234567890",
        )

        assert subscriber.subscription_status == SubscriptionStatus.PENDING
        assert subscriber.total_messages_sent == 0
        assert subscriber.total_responses == 0
        assert subscriber.opt_in_timestamp is None
        assert subscriber.opt_out_timestamp is None

    def test_to_dynamodb_item(self):
        """Test conversion to DynamoDB item."""
        subscriber = Subscriber(
            subscriber_id="sub-123",
            phone_number="+1234567890",
            subscription_status=SubscriptionStatus.ACTIVE,
        )

        item = subscriber.to_dynamodb_item()

        assert item["subscriber_id"]["S"] == "sub-123"
        assert item["phone_number"]["S"] == "+1234567890"
        assert item["subscription_status"]["S"] == "active"


class TestAnalyticsMetrics:
    """Tests for AnalyticsMetrics model."""

    def test_calculate_rates_with_data(self):
        """Test rate calculation with data."""
        metrics = AnalyticsMetrics(
            messages_sent=100,
            messages_delivered=95,
            messages_failed=5,
            responses_received=20,
        )

        metrics.calculate_rates()

        assert metrics.delivery_rate == 0.95
        assert metrics.response_rate == 0.20

    def test_calculate_rates_no_messages(self):
        """Test rate calculation with no messages."""
        metrics = AnalyticsMetrics()

        metrics.calculate_rates()

        assert metrics.delivery_rate == 0
        assert metrics.response_rate == 0
