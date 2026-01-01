"""Unit tests for analytics service."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from common.models import SMSEvent, SMSEventType
from services.analytics_service import AnalyticsService


class TestAnalyticsService:
    """Tests for AnalyticsService."""

    @pytest.fixture
    def analytics_service(self):
        """Create analytics service instance."""
        with patch("services.analytics_service.get_cloudwatch_client") as mock:
            mock.return_value = MagicMock()
            service = AnalyticsService()
            yield service

    def test_calculate_metrics_success_events(self, analytics_service):
        """Test metrics calculation for success events."""
        events = [
            SMSEvent(
                event_type="_SMS.SUCCESS",
                event_timestamp=datetime.utcnow(),
                app_id="test-app",
                price_millicents=645,
            ),
            SMSEvent(
                event_type="_SMS.SUCCESS",
                event_timestamp=datetime.utcnow(),
                app_id="test-app",
                price_millicents=645,
            ),
        ]

        metrics = analytics_service.calculate_metrics(events)

        assert metrics.messages_delivered == 2
        assert metrics.messages_sent == 2
        assert metrics.messages_failed == 0
        assert metrics.delivery_rate == 1.0

    def test_calculate_metrics_mixed_events(self, analytics_service):
        """Test metrics calculation for mixed events."""
        events = [
            SMSEvent(
                event_type="_SMS.SUCCESS",
                event_timestamp=datetime.utcnow(),
                app_id="test-app",
                price_millicents=645,
            ),
            SMSEvent(
                event_type="_SMS.FAILURE",
                event_timestamp=datetime.utcnow(),
                app_id="test-app",
                price_millicents=0,
            ),
            SMSEvent(
                event_type="_SMS.OPTOUT",
                event_timestamp=datetime.utcnow(),
                app_id="test-app",
                price_millicents=0,
            ),
            SMSEvent(
                event_type="_SMS.RECEIVED",
                event_timestamp=datetime.utcnow(),
                app_id="test-app",
                price_millicents=0,
            ),
        ]

        metrics = analytics_service.calculate_metrics(events)

        assert metrics.messages_delivered == 1
        assert metrics.messages_sent == 2
        assert metrics.messages_failed == 1
        assert metrics.opt_outs == 1
        assert metrics.responses_received == 1
        assert metrics.delivery_rate == 0.5

    def test_calculate_metrics_cost(self, analytics_service):
        """Test cost calculation."""
        events = [
            SMSEvent(
                event_type="_SMS.SUCCESS",
                event_timestamp=datetime.utcnow(),
                app_id="test-app",
                price_millicents=1000,  # 0.01 USD
            ),
            SMSEvent(
                event_type="_SMS.SUCCESS",
                event_timestamp=datetime.utcnow(),
                app_id="test-app",
                price_millicents=2000,  # 0.02 USD
            ),
        ]

        metrics = analytics_service.calculate_metrics(events)

        assert metrics.total_cost_usd == pytest.approx(0.03, rel=1e-6)

    def test_analyze_response_sentiment_positive(self, analytics_service):
        """Test positive sentiment detection."""
        assert analytics_service.analyze_response_sentiment("YES") == "positive"
        assert analytics_service.analyze_response_sentiment("thanks!") == "positive"
        assert analytics_service.analyze_response_sentiment("I love it") == "positive"
        assert analytics_service.analyze_response_sentiment("Great, interested") == "positive"

    def test_analyze_response_sentiment_negative(self, analytics_service):
        """Test negative sentiment detection."""
        assert analytics_service.analyze_response_sentiment("STOP") == "negative"
        assert analytics_service.analyze_response_sentiment("no thanks") == "negative"
        assert analytics_service.analyze_response_sentiment("unsubscribe") == "negative"
        assert analytics_service.analyze_response_sentiment("This is spam") == "negative"

    def test_analyze_response_sentiment_neutral(self, analytics_service):
        """Test neutral sentiment detection."""
        assert analytics_service.analyze_response_sentiment("Hello") == "neutral"
        assert analytics_service.analyze_response_sentiment("What time?") == "neutral"
        assert analytics_service.analyze_response_sentiment("123") == "neutral"
