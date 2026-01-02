"""Analytics service for real-time metrics processing."""

from datetime import datetime

from aws_lambda_powertools import Logger

from common.clients import get_cloudwatch_client
from common.config import settings
from common.models import SMSEvent, SMSEventType, AnalyticsMetrics

logger = Logger()


class AnalyticsService:
    """Service for real-time analytics processing."""

    def __init__(self) -> None:
        self.cloudwatch = get_cloudwatch_client()
        self.namespace = "SMS/Marketing"

    def calculate_metrics(self, events: list[SMSEvent]) -> AnalyticsMetrics:
        """Calculate metrics from a batch of events."""
        metrics = AnalyticsMetrics()

        for event in events:
            if event.event_type == SMSEventType.SUCCESS.value:
                metrics.messages_delivered += 1
                metrics.messages_sent += 1
            elif event.event_type == SMSEventType.FAILURE.value:
                metrics.messages_failed += 1
                metrics.messages_sent += 1
            elif event.event_type == SMSEventType.OPTOUT.value:
                metrics.opt_outs += 1
            elif event.event_type == SMSEventType.RECEIVED.value:
                metrics.responses_received += 1

            # Accumulate cost
            metrics.total_cost_usd += event.price_millicents / 100000

        metrics.calculate_rates()
        return metrics

    def publish_metrics(self, metrics: AnalyticsMetrics) -> None:
        """Publish metrics to CloudWatch."""
        try:
            metric_data = [
                {
                    "MetricName": "MessagesDelivered",
                    "Value": metrics.messages_delivered,
                    "Unit": "Count",
                    "Timestamp": metrics.timestamp,
                },
                {
                    "MetricName": "MessagesFailed",
                    "Value": metrics.messages_failed,
                    "Unit": "Count",
                    "Timestamp": metrics.timestamp,
                },
                {
                    "MetricName": "ResponsesReceived",
                    "Value": metrics.responses_received,
                    "Unit": "Count",
                    "Timestamp": metrics.timestamp,
                },
                {
                    "MetricName": "OptOuts",
                    "Value": metrics.opt_outs,
                    "Unit": "Count",
                    "Timestamp": metrics.timestamp,
                },
                {
                    "MetricName": "DeliveryRate",
                    "Value": metrics.delivery_rate * 100,
                    "Unit": "Percent",
                    "Timestamp": metrics.timestamp,
                },
                {
                    "MetricName": "ResponseRate",
                    "Value": metrics.response_rate * 100,
                    "Unit": "Percent",
                    "Timestamp": metrics.timestamp,
                },
                {
                    "MetricName": "TotalCostUSD",
                    "Value": metrics.total_cost_usd,
                    "Unit": "None",
                    "Timestamp": metrics.timestamp,
                },
            ]

            # Filter out zero-value metrics
            metric_data = [m for m in metric_data if m["Value"] > 0]

            if metric_data:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data,
                )

                logger.info(
                    "Published metrics to CloudWatch",
                    extra={
                        "metrics_count": len(metric_data),
                        "delivered": metrics.messages_delivered,
                        "failed": metrics.messages_failed,
                        "responses": metrics.responses_received,
                    },
                )

        except Exception as e:
            logger.error(f"Failed to publish metrics: {e}")

    def publish_campaign_metrics(
        self,
        campaign_id: str,
        events: list[SMSEvent],
    ) -> None:
        """Publish campaign-specific metrics."""
        metrics = self.calculate_metrics(events)

        try:
            metric_data = [
                {
                    "MetricName": "CampaignMessagesDelivered",
                    "Value": metrics.messages_delivered,
                    "Unit": "Count",
                    "Timestamp": metrics.timestamp,
                    "Dimensions": [
                        {"Name": "CampaignId", "Value": campaign_id},
                    ],
                },
                {
                    "MetricName": "CampaignDeliveryRate",
                    "Value": metrics.delivery_rate * 100,
                    "Unit": "Percent",
                    "Timestamp": metrics.timestamp,
                    "Dimensions": [
                        {"Name": "CampaignId", "Value": campaign_id},
                    ],
                },
            ]

            # Filter out zero-value metrics
            metric_data = [m for m in metric_data if m["Value"] > 0]

            if metric_data:
                self.cloudwatch.put_metric_data(
                    Namespace=self.namespace,
                    MetricData=metric_data,
                )

        except Exception as e:
            logger.error(f"Failed to publish campaign metrics: {e}")

    def analyze_response_sentiment(self, response_text: str) -> str:
        """Simple sentiment analysis for SMS responses."""
        positive_keywords = {
            "yes", "y", "ok", "great", "thanks", "thank", "love", "awesome",
            "confirm", "interested", "buy", "want", "order", "1",
        }
        negative_keywords = {
            "no", "n", "stop", "cancel", "unsubscribe", "hate", "spam",
            "never", "remove", "delete", "quit", "end", "0",
        }

        normalized = response_text.lower().strip()
        words = set(normalized.split())

        if words & positive_keywords:
            return "positive"
        elif words & negative_keywords:
            return "negative"
        else:
            return "neutral"
