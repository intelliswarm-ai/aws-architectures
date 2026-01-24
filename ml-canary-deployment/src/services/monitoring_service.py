"""Service for monitoring SageMaker endpoint metrics."""

from datetime import datetime, timedelta
from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import AWSClients
from src.common.config import Settings
from src.common.exceptions import MonitoringError
from src.common.models import DeploymentStatus, EndpointMetrics
from src.common.utils import calculate_error_rate

logger = Logger()


class MonitoringService:
    """Service for monitoring SageMaker endpoint performance metrics."""

    def __init__(self, clients: AWSClients, settings: Settings):
        """Initialize monitoring service.

        Args:
            clients: AWS clients instance.
            settings: Application settings.
        """
        self.clients = clients
        self.settings = settings
        self._deployments_table = settings.deployments_table
        self._metrics_table = settings.metrics_table
        self._namespace = "AWS/SageMaker"

    def get_variant_metrics(
        self,
        endpoint_name: str,
        variant_name: str,
        period_minutes: int = 5,
    ) -> EndpointMetrics:
        """Get CloudWatch metrics for a specific variant.

        Args:
            endpoint_name: SageMaker endpoint name.
            variant_name: Production variant name.
            period_minutes: Metric aggregation period.

        Returns:
            EndpointMetrics with collected metrics.

        Raises:
            MonitoringError: On metric collection failure.
        """
        logger.debug(
            "Collecting variant metrics",
            endpoint_name=endpoint_name,
            variant_name=variant_name,
        )

        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=period_minutes)
            period = period_minutes * 60  # Convert to seconds

            dimensions = [
                {"Name": "EndpointName", "Value": endpoint_name},
                {"Name": "VariantName", "Value": variant_name},
            ]

            # Collect all metrics
            invocation_count = self._get_metric_sum(
                "Invocations", dimensions, start_time, end_time, period
            )
            error_4xx = self._get_metric_sum(
                "Invocation4XXErrors", dimensions, start_time, end_time, period
            )
            error_5xx = self._get_metric_sum(
                "Invocation5XXErrors", dimensions, start_time, end_time, period
            )

            # Latency metrics
            latency_p50 = self._get_metric_percentile(
                "ModelLatency", dimensions, start_time, end_time, period, 50
            )
            latency_p90 = self._get_metric_percentile(
                "ModelLatency", dimensions, start_time, end_time, period, 90
            )
            latency_p99 = self._get_metric_percentile(
                "ModelLatency", dimensions, start_time, end_time, period, 99
            )
            overhead_latency = self._get_metric_average(
                "OverheadLatency", dimensions, start_time, end_time, period
            )

            # Resource utilization
            cpu_util = self._get_metric_average(
                "CPUUtilization", dimensions, start_time, end_time, period
            )
            memory_util = self._get_metric_average(
                "MemoryUtilization", dimensions, start_time, end_time, period
            )
            disk_util = self._get_metric_average(
                "DiskUtilization", dimensions, start_time, end_time, period
            )

            # Calculate error rate
            error_rate = calculate_error_rate(
                int(invocation_count), int(error_4xx), int(error_5xx)
            )

            # Convert latency from microseconds to milliseconds
            return EndpointMetrics(
                variant_name=variant_name,
                endpoint_name=endpoint_name,
                invocation_count=int(invocation_count),
                invocation_4xx_errors=int(error_4xx),
                invocation_5xx_errors=int(error_5xx),
                model_latency_p50_ms=latency_p50 / 1000 if latency_p50 else 0.0,
                model_latency_p90_ms=latency_p90 / 1000 if latency_p90 else 0.0,
                model_latency_p99_ms=latency_p99 / 1000 if latency_p99 else 0.0,
                overhead_latency_ms=overhead_latency / 1000 if overhead_latency else 0.0,
                cpu_utilization=cpu_util,
                memory_utilization=memory_util,
                disk_utilization=disk_util,
                error_rate=error_rate,
            )

        except ClientError as e:
            raise MonitoringError(
                f"Failed to collect metrics: {e}",
                endpoint_name=endpoint_name,
                metric_name="multiple",
            )

    def _get_metric_sum(
        self,
        metric_name: str,
        dimensions: list[dict],
        start_time: datetime,
        end_time: datetime,
        period: int,
    ) -> float:
        """Get sum statistic for a metric.

        Args:
            metric_name: CloudWatch metric name.
            dimensions: Metric dimensions.
            start_time: Query start time.
            end_time: Query end time.
            period: Aggregation period in seconds.

        Returns:
            Sum value or 0.0 if no data.
        """
        response = self.clients.cloudwatch.get_metric_statistics(
            Namespace=self._namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=["Sum"],
        )
        datapoints = response.get("Datapoints", [])
        if datapoints:
            return sum(dp.get("Sum", 0) for dp in datapoints)
        return 0.0

    def _get_metric_average(
        self,
        metric_name: str,
        dimensions: list[dict],
        start_time: datetime,
        end_time: datetime,
        period: int,
    ) -> float:
        """Get average statistic for a metric.

        Args:
            metric_name: CloudWatch metric name.
            dimensions: Metric dimensions.
            start_time: Query start time.
            end_time: Query end time.
            period: Aggregation period in seconds.

        Returns:
            Average value or 0.0 if no data.
        """
        response = self.clients.cloudwatch.get_metric_statistics(
            Namespace=self._namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            Statistics=["Average"],
        )
        datapoints = response.get("Datapoints", [])
        if datapoints:
            return datapoints[-1].get("Average", 0.0)
        return 0.0

    def _get_metric_percentile(
        self,
        metric_name: str,
        dimensions: list[dict],
        start_time: datetime,
        end_time: datetime,
        period: int,
        percentile: int,
    ) -> float:
        """Get percentile statistic for a metric.

        Args:
            metric_name: CloudWatch metric name.
            dimensions: Metric dimensions.
            start_time: Query start time.
            end_time: Query end time.
            period: Aggregation period in seconds.
            percentile: Percentile value (e.g., 50, 90, 99).

        Returns:
            Percentile value or 0.0 if no data.
        """
        response = self.clients.cloudwatch.get_metric_statistics(
            Namespace=self._namespace,
            MetricName=metric_name,
            Dimensions=dimensions,
            StartTime=start_time,
            EndTime=end_time,
            Period=period,
            ExtendedStatistics=[f"p{percentile}"],
        )
        datapoints = response.get("Datapoints", [])
        if datapoints:
            return datapoints[-1].get("ExtendedStatistics", {}).get(f"p{percentile}", 0.0)
        return 0.0

    def get_active_deployments(self) -> list[dict[str, Any]]:
        """Get list of active deployments to monitor.

        Returns:
            List of active deployment records.
        """
        try:
            table = self.clients.dynamodb_resource.Table(self._deployments_table)

            response = table.scan(
                FilterExpression="#status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={
                    ":status": DeploymentStatus.IN_PROGRESS.value
                },
            )

            return response.get("Items", [])

        except ClientError as e:
            logger.error("Failed to get active deployments", error=str(e))
            return []

    def store_metrics(
        self,
        deployment_id: str,
        metrics: EndpointMetrics,
    ) -> None:
        """Store metrics snapshot for analysis.

        Args:
            deployment_id: Deployment identifier.
            metrics: Collected metrics.
        """
        try:
            table = self.clients.dynamodb_resource.Table(self._metrics_table)
            table.put_item(Item={
                "deployment_id": deployment_id,
                "timestamp": metrics.timestamp.isoformat(),
                "variant_name": metrics.variant_name,
                "endpoint_name": metrics.endpoint_name,
                "invocation_count": metrics.invocation_count,
                "error_rate": str(metrics.error_rate),
                "p50_latency_ms": str(metrics.model_latency_p50_ms),
                "p90_latency_ms": str(metrics.model_latency_p90_ms),
                "p99_latency_ms": str(metrics.model_latency_p99_ms),
                "cpu_utilization": str(metrics.cpu_utilization),
                "memory_utilization": str(metrics.memory_utilization),
            })
        except ClientError as e:
            logger.warning("Failed to store metrics", error=str(e))

    def trigger_rollback(
        self,
        deployment_id: str,
        reason: str,
        metrics: EndpointMetrics,
    ) -> None:
        """Trigger automatic rollback via EventBridge.

        Args:
            deployment_id: Deployment identifier.
            reason: Rollback reason.
            metrics: Current metrics snapshot.
        """
        logger.warning(
            "Triggering automatic rollback",
            deployment_id=deployment_id,
            reason=reason,
        )

        try:
            self.clients.events.put_events(
                Entries=[{
                    "Source": "ml-canary-deployment",
                    "DetailType": "AutoRollbackTriggered",
                    "Detail": f'{{"deployment_id": "{deployment_id}", "reason": "{reason}", '
                             f'"error_rate": {metrics.error_rate}, '
                             f'"p99_latency_ms": {metrics.model_latency_p99_ms}}}',
                }]
            )
        except ClientError as e:
            logger.error(
                "Failed to trigger rollback event",
                deployment_id=deployment_id,
                error=str(e),
            )

    def create_dashboard(
        self,
        deployment_id: str,
        endpoint_name: str,
        variants: list[str],
    ) -> str:
        """Create CloudWatch dashboard for deployment monitoring.

        Args:
            deployment_id: Deployment identifier.
            endpoint_name: Endpoint name.
            variants: List of variant names to monitor.

        Returns:
            Dashboard name.
        """
        dashboard_name = f"Canary-{deployment_id[:20]}"

        widgets = []
        row = 0

        for variant in variants:
            # Latency widget
            widgets.append({
                "type": "metric",
                "x": 0,
                "y": row,
                "width": 12,
                "height": 6,
                "properties": {
                    "title": f"{variant} - Latency",
                    "metrics": [
                        [self._namespace, "ModelLatency", "EndpointName", endpoint_name,
                         "VariantName", variant, {"stat": "p99", "label": "P99"}],
                        ["...", {"stat": "p90", "label": "P90"}],
                        ["...", {"stat": "p50", "label": "P50"}],
                    ],
                    "period": 60,
                    "region": self.settings.aws_region,
                },
            })

            # Error rate widget
            widgets.append({
                "type": "metric",
                "x": 12,
                "y": row,
                "width": 12,
                "height": 6,
                "properties": {
                    "title": f"{variant} - Errors",
                    "metrics": [
                        [self._namespace, "Invocation4XXErrors", "EndpointName", endpoint_name,
                         "VariantName", variant],
                        [self._namespace, "Invocation5XXErrors", "EndpointName", endpoint_name,
                         "VariantName", variant],
                    ],
                    "period": 60,
                    "region": self.settings.aws_region,
                },
            })

            row += 6

        dashboard_body = {"widgets": widgets}

        self.clients.cloudwatch.put_dashboard(
            DashboardName=dashboard_name,
            DashboardBody=str(dashboard_body).replace("'", '"'),
        )

        return dashboard_name
