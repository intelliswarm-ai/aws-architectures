"""Handler for monitoring endpoint performance metrics."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import MonitoringError
from src.common.models import EndpointMetrics
from src.common.utils import json_serialize
from src.services.monitoring_service import MonitoringService
from src.services.notification_service import NotificationService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Handle endpoint monitoring and alerting.

    Collects CloudWatch metrics for SageMaker endpoints, evaluates health,
    and triggers alerts or auto-rollback when thresholds are exceeded.

    Triggered by EventBridge schedule to run every minute during deployments.

    Args:
        event: EventBridge event or direct invocation event.
        context: Lambda context object.

    Returns:
        Response with monitoring results.
    """
    logger.info("Starting endpoint monitoring")

    try:
        settings = get_settings()
        clients = get_clients()
        monitoring_service = MonitoringService(clients, settings)
        notification_service = NotificationService(clients, settings)

        # Get active deployments to monitor
        active_deployments = monitoring_service.get_active_deployments()

        if not active_deployments:
            logger.info("No active deployments to monitor")
            return {
                "statusCode": 200,
                "body": json_serialize({"message": "No active deployments"}),
            }

        monitoring_results = []

        for deployment in active_deployments:
            try:
                result = _monitor_deployment(
                    deployment,
                    monitoring_service,
                    notification_service,
                    settings,
                )
                monitoring_results.append(result)
            except Exception as e:
                logger.error(
                    "Error monitoring deployment",
                    deployment_id=deployment["deployment_id"],
                    error=str(e),
                )
                monitoring_results.append({
                    "deployment_id": deployment["deployment_id"],
                    "status": "error",
                    "error": str(e),
                })

        return {
            "statusCode": 200,
            "body": json_serialize({
                "monitored_deployments": len(monitoring_results),
                "results": monitoring_results,
            }),
        }

    except MonitoringError as e:
        logger.error("Monitoring error", error=str(e))
        return {"statusCode": 500, "body": json_serialize(e.to_dict())}

    except Exception as e:
        logger.exception("Unexpected monitoring error")
        return {"statusCode": 500, "body": json_serialize({"error": str(e)})}


def _monitor_deployment(
    deployment: dict[str, Any],
    monitoring_service: MonitoringService,
    notification_service: NotificationService,
    settings: Any,
) -> dict[str, Any]:
    """Monitor a single deployment.

    Args:
        deployment: Deployment configuration.
        monitoring_service: Monitoring service instance.
        notification_service: Notification service instance.
        settings: Application settings.

    Returns:
        Monitoring result for the deployment.
    """
    deployment_id = deployment["deployment_id"]
    endpoint_name = deployment["endpoint_name"]
    canary_variant = deployment.get("canary_variant", {})
    current_variant = deployment.get("current_variant", {})

    logger.info(
        "Monitoring deployment",
        deployment_id=deployment_id,
        endpoint_name=endpoint_name,
    )

    # Collect metrics for both variants
    canary_metrics = monitoring_service.get_variant_metrics(
        endpoint_name=endpoint_name,
        variant_name=canary_variant.get("variant_name", "canary"),
    )

    current_metrics = monitoring_service.get_variant_metrics(
        endpoint_name=endpoint_name,
        variant_name=current_variant.get("variant_name", "production"),
    )

    # Evaluate canary health
    health_evaluation = _evaluate_health(
        canary_metrics=canary_metrics,
        current_metrics=current_metrics,
        latency_threshold=deployment.get("latency_threshold_ms", settings.latency_threshold_ms),
        error_rate_threshold=deployment.get(
            "error_rate_threshold", settings.error_rate_threshold
        ),
    )

    # Store metrics for analysis
    monitoring_service.store_metrics(deployment_id, canary_metrics)
    monitoring_service.store_metrics(deployment_id, current_metrics)

    # Check for alerts
    alerts = []
    if health_evaluation["canary_unhealthy"]:
        alert = _create_alert(
            deployment_id=deployment_id,
            endpoint_name=endpoint_name,
            variant_name=canary_metrics.variant_name,
            reason=health_evaluation["reason"],
            metrics=canary_metrics,
        )
        alerts.append(alert)

        # Send alert notification
        notification_service.send_alert(alert)

        # Check if auto-rollback is enabled
        if deployment.get("auto_rollback_enabled", True):
            logger.warning(
                "Triggering auto-rollback",
                deployment_id=deployment_id,
                reason=health_evaluation["reason"],
            )
            monitoring_service.trigger_rollback(
                deployment_id=deployment_id,
                reason=health_evaluation["reason"],
                metrics=canary_metrics,
            )

    result = {
        "deployment_id": deployment_id,
        "endpoint_name": endpoint_name,
        "status": "healthy" if not health_evaluation["canary_unhealthy"] else "unhealthy",
        "canary_metrics": {
            "variant_name": canary_metrics.variant_name,
            "invocation_count": canary_metrics.invocation_count,
            "error_rate": canary_metrics.error_rate,
            "p99_latency_ms": canary_metrics.model_latency_p99_ms,
        },
        "current_metrics": {
            "variant_name": current_metrics.variant_name,
            "invocation_count": current_metrics.invocation_count,
            "error_rate": current_metrics.error_rate,
            "p99_latency_ms": current_metrics.model_latency_p99_ms,
        },
        "alerts": alerts,
    }

    logger.info(
        "Monitoring complete",
        deployment_id=deployment_id,
        status=result["status"],
        canary_error_rate=canary_metrics.error_rate,
        canary_p99_latency=canary_metrics.model_latency_p99_ms,
    )

    return result


def _evaluate_health(
    canary_metrics: EndpointMetrics,
    current_metrics: EndpointMetrics,
    latency_threshold: float,
    error_rate_threshold: float,
) -> dict[str, Any]:
    """Evaluate canary variant health against thresholds.

    Args:
        canary_metrics: Metrics for canary variant.
        current_metrics: Metrics for current production variant.
        latency_threshold: Maximum acceptable P99 latency in ms.
        error_rate_threshold: Maximum acceptable error rate.

    Returns:
        Health evaluation result.
    """
    reasons = []
    canary_unhealthy = False

    # Check latency threshold
    if canary_metrics.model_latency_p99_ms > latency_threshold:
        canary_unhealthy = True
        reasons.append(
            f"P99 latency {canary_metrics.model_latency_p99_ms:.1f}ms exceeds "
            f"threshold {latency_threshold:.1f}ms"
        )

    # Check error rate threshold
    if canary_metrics.error_rate > error_rate_threshold:
        canary_unhealthy = True
        reasons.append(
            f"Error rate {canary_metrics.error_rate:.2%} exceeds "
            f"threshold {error_rate_threshold:.2%}"
        )

    # Compare with current production (if canary is significantly worse)
    if current_metrics.invocation_count > 100:  # Only compare if we have enough data
        latency_ratio = (
            canary_metrics.model_latency_p99_ms / max(current_metrics.model_latency_p99_ms, 1)
        )
        if latency_ratio > 2.0:
            canary_unhealthy = True
            reasons.append(
                f"Canary latency is {latency_ratio:.1f}x worse than production"
            )

        error_diff = canary_metrics.error_rate - current_metrics.error_rate
        if error_diff > 0.05:  # 5% higher error rate
            canary_unhealthy = True
            reasons.append(
                f"Canary error rate is {error_diff:.2%} higher than production"
            )

    return {
        "canary_unhealthy": canary_unhealthy,
        "reason": "; ".join(reasons) if reasons else "Healthy",
    }


def _create_alert(
    deployment_id: str,
    endpoint_name: str,
    variant_name: str,
    reason: str,
    metrics: EndpointMetrics,
) -> dict[str, Any]:
    """Create an alert for unhealthy variant.

    Args:
        deployment_id: Deployment identifier.
        endpoint_name: Endpoint name.
        variant_name: Variant name.
        reason: Alert reason.
        metrics: Current metrics.

    Returns:
        Alert dictionary.
    """
    return {
        "type": "VARIANT_UNHEALTHY",
        "deployment_id": deployment_id,
        "endpoint_name": endpoint_name,
        "variant_name": variant_name,
        "reason": reason,
        "metrics": {
            "invocation_count": metrics.invocation_count,
            "error_rate": metrics.error_rate,
            "p99_latency_ms": metrics.model_latency_p99_ms,
            "p90_latency_ms": metrics.model_latency_p90_ms,
            "p50_latency_ms": metrics.model_latency_p50_ms,
        },
        "severity": "HIGH",
    }
