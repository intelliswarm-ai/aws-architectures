"""Service for sending notifications about deployment events."""

from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import AWSClients
from src.common.config import Settings
from src.common.models import DeploymentConfig, RollbackEvent, TrafficShiftEvent
from src.common.utils import json_serialize

logger = Logger()


class NotificationService:
    """Service for sending SNS notifications about deployment events."""

    def __init__(self, clients: AWSClients, settings: Settings):
        """Initialize notification service.

        Args:
            clients: AWS clients instance.
            settings: Application settings.
        """
        self.clients = clients
        self.settings = settings
        self._alerts_topic = settings.alerts_topic_arn
        self._events_topic = settings.deployment_events_topic_arn

    def send_deployment_started(self, config: DeploymentConfig) -> None:
        """Send notification when deployment starts.

        Args:
            config: Deployment configuration.
        """
        self._publish_event(
            subject="Canary Deployment Started",
            message={
                "event_type": "DEPLOYMENT_STARTED",
                "deployment_id": config.deployment_id,
                "endpoint_name": config.endpoint_name,
                "canary_variant": config.canary_variant.variant_name,
                "canary_model": config.canary_variant.model_name,
                "initial_traffic": config.canary_variant.initial_weight,
                "auto_rollback_enabled": config.auto_rollback_enabled,
            },
        )

    def send_deployment_completed(
        self,
        deployment_id: str,
        endpoint_name: str,
    ) -> None:
        """Send notification when deployment completes successfully.

        Args:
            deployment_id: Deployment identifier.
            endpoint_name: Endpoint name.
        """
        self._publish_event(
            subject="Canary Deployment Completed",
            message={
                "event_type": "DEPLOYMENT_COMPLETED",
                "deployment_id": deployment_id,
                "endpoint_name": endpoint_name,
                "status": "SUCCESS",
            },
        )

    def send_deployment_cancelled(
        self,
        deployment_id: str,
        reason: str,
    ) -> None:
        """Send notification when deployment is cancelled.

        Args:
            deployment_id: Deployment identifier.
            reason: Cancellation reason.
        """
        self._publish_event(
            subject="Canary Deployment Cancelled",
            message={
                "event_type": "DEPLOYMENT_CANCELLED",
                "deployment_id": deployment_id,
                "reason": reason,
            },
        )

    def send_traffic_shift_notification(self, event: TrafficShiftEvent) -> None:
        """Send notification when traffic is shifted.

        Args:
            event: Traffic shift event details.
        """
        self._publish_event(
            subject="Traffic Shift Completed",
            message={
                "event_type": "TRAFFIC_SHIFTED",
                "deployment_id": event.deployment_id,
                "from_weights": event.from_weights,
                "to_weights": event.to_weights,
                "reason": event.reason,
                "triggered_by": event.triggered_by,
            },
        )

    def send_rollback_notification(self, event: RollbackEvent) -> None:
        """Send notification when rollback occurs.

        Args:
            event: Rollback event details.
        """
        # Send to alerts topic for immediate attention
        self._publish_alert(
            subject="ALERT: Canary Deployment Rollback",
            message={
                "event_type": "ROLLBACK",
                "deployment_id": event.deployment_id,
                "reason": event.reason,
                "automatic": event.automatic,
                "triggered_by": event.triggered_by,
                "metrics": {
                    "error_rate": event.metrics_snapshot.error_rate,
                    "p99_latency_ms": event.metrics_snapshot.model_latency_p99_ms,
                    "invocation_count": event.metrics_snapshot.invocation_count,
                },
            },
            severity="HIGH",
        )

    def send_alert(self, alert: dict[str, Any]) -> None:
        """Send a monitoring alert.

        Args:
            alert: Alert details.
        """
        severity = alert.get("severity", "MEDIUM")

        self._publish_alert(
            subject=f"ALERT [{severity}]: {alert.get('type', 'Unknown')}",
            message=alert,
            severity=severity,
        )

    def send_health_check_failure(
        self,
        endpoint_name: str,
        variant_name: str,
        reason: str,
        metrics: dict[str, Any],
    ) -> None:
        """Send notification when variant health check fails.

        Args:
            endpoint_name: Endpoint name.
            variant_name: Variant name.
            reason: Failure reason.
            metrics: Current metrics.
        """
        self._publish_alert(
            subject=f"ALERT: Variant Health Check Failed - {variant_name}",
            message={
                "event_type": "HEALTH_CHECK_FAILURE",
                "endpoint_name": endpoint_name,
                "variant_name": variant_name,
                "reason": reason,
                "metrics": metrics,
            },
            severity="HIGH",
        )

    def send_threshold_breach(
        self,
        deployment_id: str,
        endpoint_name: str,
        variant_name: str,
        metric_name: str,
        current_value: float,
        threshold: float,
    ) -> None:
        """Send notification when a threshold is breached.

        Args:
            deployment_id: Deployment identifier.
            endpoint_name: Endpoint name.
            variant_name: Variant name.
            metric_name: Name of the breached metric.
            current_value: Current metric value.
            threshold: Configured threshold.
        """
        self._publish_alert(
            subject=f"ALERT: Threshold Breach - {metric_name}",
            message={
                "event_type": "THRESHOLD_BREACH",
                "deployment_id": deployment_id,
                "endpoint_name": endpoint_name,
                "variant_name": variant_name,
                "metric_name": metric_name,
                "current_value": current_value,
                "threshold": threshold,
                "breach_percentage": ((current_value / threshold) - 1) * 100,
            },
            severity="HIGH",
        )

    def _publish_event(self, subject: str, message: dict[str, Any]) -> None:
        """Publish event to events topic.

        Args:
            subject: Message subject.
            message: Message body.
        """
        if not self._events_topic:
            logger.warning("Events topic not configured, skipping notification")
            return

        try:
            self.clients.sns.publish(
                TopicArn=self._events_topic,
                Subject=subject,
                Message=json_serialize(message),
                MessageAttributes={
                    "event_type": {
                        "DataType": "String",
                        "StringValue": message.get("event_type", "UNKNOWN"),
                    },
                },
            )
            logger.debug("Published event notification", subject=subject)

        except ClientError as e:
            logger.warning(
                "Failed to publish event notification",
                error=str(e),
                subject=subject,
            )

    def _publish_alert(
        self,
        subject: str,
        message: dict[str, Any],
        severity: str = "MEDIUM",
    ) -> None:
        """Publish alert to alerts topic.

        Args:
            subject: Message subject.
            message: Message body.
            severity: Alert severity level.
        """
        if not self._alerts_topic:
            logger.warning("Alerts topic not configured, skipping alert")
            return

        try:
            self.clients.sns.publish(
                TopicArn=self._alerts_topic,
                Subject=subject,
                Message=json_serialize(message),
                MessageAttributes={
                    "severity": {
                        "DataType": "String",
                        "StringValue": severity,
                    },
                    "event_type": {
                        "DataType": "String",
                        "StringValue": message.get("event_type", "ALERT"),
                    },
                },
            )
            logger.info("Published alert", subject=subject, severity=severity)

        except ClientError as e:
            logger.error(
                "Failed to publish alert",
                error=str(e),
                subject=subject,
            )
