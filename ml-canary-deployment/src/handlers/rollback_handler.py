"""Handler for rollback operations during canary deployments."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import RollbackError, ValidationError
from src.common.models import DeploymentStatus, RollbackEvent
from src.common.utils import generate_event_id, json_serialize
from src.services.deployment_service import DeploymentService
from src.services.monitoring_service import MonitoringService
from src.services.notification_service import NotificationService
from src.services.traffic_service import TrafficService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Handle rollback operations for canary deployments.

    Supports immediate rollback (shift all traffic to production) and
    gradual rollback (progressively decrease canary traffic).

    Args:
        event: Event containing rollback configuration.
        context: Lambda context object.

    Returns:
        Response with rollback status.
    """
    action = event.get("action", "immediate")
    logger.info("Processing rollback action", action=action)

    try:
        settings = get_settings()
        clients = get_clients()
        deployment_service = DeploymentService(clients, settings)
        traffic_service = TrafficService(clients, settings)
        monitoring_service = MonitoringService(clients, settings)
        notification_service = NotificationService(clients, settings)

        if action == "immediate":
            return _handle_immediate_rollback(
                event,
                deployment_service,
                traffic_service,
                monitoring_service,
                notification_service,
            )
        elif action == "gradual":
            return _handle_gradual_rollback(
                event,
                deployment_service,
                traffic_service,
                notification_service,
            )
        elif action == "auto":
            return _handle_auto_rollback(
                event,
                deployment_service,
                traffic_service,
                monitoring_service,
                notification_service,
            )
        else:
            raise ValidationError(f"Unknown rollback action: {action}")

    except ValidationError as e:
        logger.warning("Validation error", error=str(e))
        return {"statusCode": 400, "body": json_serialize({"error": e.message})}

    except RollbackError as e:
        logger.error("Rollback error", error=str(e), details=e.to_dict())
        return {"statusCode": 500, "body": json_serialize(e.to_dict())}

    except Exception as e:
        logger.exception("Unexpected error during rollback")
        return {"statusCode": 500, "body": json_serialize({"error": str(e)})}


def _handle_immediate_rollback(
    event: dict[str, Any],
    deployment_service: DeploymentService,
    traffic_service: TrafficService,
    monitoring_service: MonitoringService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Handle immediate rollback by shifting all traffic to production.

    Args:
        event: Event containing deployment ID and reason.
        deployment_service: Deployment service instance.
        traffic_service: Traffic service instance.
        monitoring_service: Monitoring service instance.
        notification_service: Notification service instance.

    Returns:
        Response with rollback status.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    reason = event.get("reason", "Manual immediate rollback")
    triggered_by = event.get("triggered_by", "manual")

    logger.warning(
        "Executing immediate rollback",
        deployment_id=deployment_id,
        reason=reason,
    )

    # Get deployment configuration
    deployment = deployment_service.get_deployment(deployment_id)
    endpoint_name = deployment["endpoint_name"]
    canary_variant = deployment["canary_variant"]["variant_name"]
    current_variant = deployment["current_variant"]["variant_name"]

    # Get current metrics for recording
    canary_metrics = monitoring_service.get_variant_metrics(
        endpoint_name=endpoint_name,
        variant_name=canary_variant,
    )

    # Set all traffic to production variant
    rollback_weights = {
        current_variant: 1.0,
        canary_variant: 0.0,
    }

    traffic_service.update_variant_weights(endpoint_name, rollback_weights)

    # Update deployment status
    deployment_service.update_deployment_status(
        deployment_id=deployment_id,
        status=DeploymentStatus.ROLLING_BACK,
    )

    # Record rollback event
    rollback_event = RollbackEvent(
        deployment_id=deployment_id,
        event_id=generate_event_id(),
        reason=reason,
        metrics_snapshot=canary_metrics,
        triggered_by=triggered_by,
        automatic=triggered_by == "auto_rollback",
    )
    deployment_service.record_rollback_event(rollback_event)

    # Send notification
    notification_service.send_rollback_notification(rollback_event)

    # Mark deployment as rolled back
    deployment_service.update_deployment_status(
        deployment_id=deployment_id,
        status=DeploymentStatus.ROLLED_BACK,
    )

    logger.info(
        "Immediate rollback completed",
        deployment_id=deployment_id,
        endpoint_name=endpoint_name,
    )

    return {
        "statusCode": 200,
        "body": json_serialize({
            "deployment_id": deployment_id,
            "endpoint_name": endpoint_name,
            "status": DeploymentStatus.ROLLED_BACK.value,
            "rollback_type": "immediate",
            "reason": reason,
            "weights": rollback_weights,
        }),
    }


def _handle_gradual_rollback(
    event: dict[str, Any],
    deployment_service: DeploymentService,
    traffic_service: TrafficService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Handle gradual rollback by progressively reducing canary traffic.

    Args:
        event: Event containing deployment ID and step size.
        deployment_service: Deployment service instance.
        traffic_service: Traffic service instance.
        notification_service: Notification service instance.

    Returns:
        Response with rollback progress.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    step_size = event.get("step_size", 0.2)  # Default 20% reduction per step
    reason = event.get("reason", "Manual gradual rollback")

    logger.info(
        "Executing gradual rollback step",
        deployment_id=deployment_id,
        step_size=step_size,
    )

    # Get deployment configuration
    deployment = deployment_service.get_deployment(deployment_id)
    endpoint_name = deployment["endpoint_name"]
    canary_variant = deployment["canary_variant"]["variant_name"]
    current_variant = deployment["current_variant"]["variant_name"]

    # Get current weights
    current_weights = traffic_service.get_variant_weights(endpoint_name)
    canary_weight = current_weights.get(canary_variant, 0.0)

    # Calculate new weights
    new_canary_weight = max(canary_weight - step_size, 0.0)
    new_production_weight = 1.0 - new_canary_weight

    new_weights = {
        current_variant: new_production_weight,
        canary_variant: new_canary_weight,
    }

    # Update traffic weights
    traffic_service.update_variant_weights(endpoint_name, new_weights)

    # Check if rollback is complete
    rollback_complete = new_canary_weight <= 0.0

    if rollback_complete:
        deployment_service.update_deployment_status(
            deployment_id=deployment_id,
            status=DeploymentStatus.ROLLED_BACK,
        )
        logger.info("Gradual rollback completed", deployment_id=deployment_id)
    else:
        deployment_service.update_deployment_status(
            deployment_id=deployment_id,
            status=DeploymentStatus.ROLLING_BACK,
        )

    return {
        "statusCode": 200,
        "body": json_serialize({
            "deployment_id": deployment_id,
            "endpoint_name": endpoint_name,
            "previous_weights": current_weights,
            "new_weights": new_weights,
            "rollback_complete": rollback_complete,
            "status": (
                DeploymentStatus.ROLLED_BACK.value
                if rollback_complete
                else DeploymentStatus.ROLLING_BACK.value
            ),
        }),
    }


def _handle_auto_rollback(
    event: dict[str, Any],
    deployment_service: DeploymentService,
    traffic_service: TrafficService,
    monitoring_service: MonitoringService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Handle automatic rollback triggered by monitoring alerts.

    This is called by the monitoring handler when thresholds are exceeded.

    Args:
        event: Event containing deployment ID and metrics.
        deployment_service: Deployment service instance.
        traffic_service: Traffic service instance.
        monitoring_service: Monitoring service instance.
        notification_service: Notification service instance.

    Returns:
        Response with auto rollback status.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    reason = event.get("reason", "Auto-rollback triggered by monitoring")
    metrics = event.get("metrics", {})

    logger.warning(
        "Executing automatic rollback",
        deployment_id=deployment_id,
        reason=reason,
        metrics=metrics,
    )

    # Delegate to immediate rollback
    event["action"] = "immediate"
    event["triggered_by"] = "auto_rollback"

    return _handle_immediate_rollback(
        event,
        deployment_service,
        traffic_service,
        monitoring_service,
        notification_service,
    )
