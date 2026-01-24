"""Handler for traffic shifting operations during canary deployments."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import TrafficShiftError, ValidationError
from src.common.models import TrafficShiftEvent
from src.common.utils import generate_event_id, json_serialize, normalize_weights
from src.services.deployment_service import DeploymentService
from src.services.monitoring_service import MonitoringService
from src.services.notification_service import NotificationService
from src.services.traffic_service import TrafficService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Handle traffic shifting between production variants.

    Uses SageMaker UpdateEndpointWeightsAndCapacities API to gradually
    shift traffic from current production to canary variant.

    Args:
        event: Event containing traffic shift configuration.
        context: Lambda context object.

    Returns:
        Response with traffic shift results.
    """
    action = event.get("action", "shift")
    logger.info("Processing traffic shift action", action=action)

    try:
        settings = get_settings()
        clients = get_clients()
        traffic_service = TrafficService(clients, settings)
        deployment_service = DeploymentService(clients, settings)
        monitoring_service = MonitoringService(clients, settings)
        notification_service = NotificationService(clients, settings)

        if action == "shift":
            return _handle_traffic_shift(
                event, traffic_service, deployment_service, notification_service
            )
        elif action == "auto_shift":
            return _handle_auto_shift(
                event,
                traffic_service,
                deployment_service,
                monitoring_service,
                notification_service,
            )
        elif action == "get_weights":
            return _handle_get_weights(event, traffic_service)
        elif action == "set_weights":
            return _handle_set_weights(event, traffic_service, notification_service)
        else:
            raise ValidationError(f"Unknown action: {action}")

    except ValidationError as e:
        logger.warning("Validation error", error=str(e))
        return {"statusCode": 400, "body": json_serialize({"error": e.message})}

    except TrafficShiftError as e:
        logger.error("Traffic shift error", error=str(e), details=e.to_dict())
        return {"statusCode": 500, "body": json_serialize(e.to_dict())}

    except Exception as e:
        logger.exception("Unexpected error during traffic shift")
        return {"statusCode": 500, "body": json_serialize({"error": str(e)})}


def _handle_traffic_shift(
    event: dict[str, Any],
    traffic_service: TrafficService,
    deployment_service: DeploymentService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Handle manual traffic shift request.

    Args:
        event: Event containing shift configuration.
        traffic_service: Traffic service instance.
        deployment_service: Deployment service instance.
        notification_service: Notification service instance.

    Returns:
        Response with shift results.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    shift_amount = event.get("shift_amount")
    if shift_amount is None:
        raise ValidationError("shift_amount is required")

    triggered_by = event.get("triggered_by", "manual")

    # Get current deployment configuration
    deployment = deployment_service.get_deployment(deployment_id)
    endpoint_name = deployment["endpoint_name"]
    canary_variant = deployment["canary_variant"]["variant_name"]
    current_variant = deployment["current_variant"]["variant_name"]

    # Get current weights
    current_weights = traffic_service.get_variant_weights(endpoint_name)

    # Calculate new weights
    canary_weight = min(
        current_weights.get(canary_variant, 0.0) + shift_amount, 1.0
    )
    production_weight = max(1.0 - canary_weight, 0.0)

    new_weights = {
        canary_variant: canary_weight,
        current_variant: production_weight,
    }
    new_weights = normalize_weights(new_weights)

    logger.info(
        "Shifting traffic",
        deployment_id=deployment_id,
        endpoint_name=endpoint_name,
        from_weights=current_weights,
        to_weights=new_weights,
    )

    # Execute traffic shift
    result = traffic_service.update_variant_weights(endpoint_name, new_weights)

    # Record event
    shift_event = TrafficShiftEvent(
        deployment_id=deployment_id,
        event_id=generate_event_id(),
        from_weights=current_weights,
        to_weights=new_weights,
        reason=f"Manual shift by {shift_amount}",
        triggered_by=triggered_by,
    )
    deployment_service.record_event(shift_event)

    # Send notification
    notification_service.send_traffic_shift_notification(shift_event)

    return {
        "statusCode": 200,
        "body": json_serialize({
            "deployment_id": deployment_id,
            "endpoint_name": endpoint_name,
            "previous_weights": current_weights,
            "new_weights": new_weights,
            "status": "completed",
        }),
    }


def _handle_auto_shift(
    event: dict[str, Any],
    traffic_service: TrafficService,
    deployment_service: DeploymentService,
    monitoring_service: MonitoringService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Handle automatic traffic shift based on canary health.

    Called by EventBridge schedule after bake time to progressively
    increase canary traffic if healthy.

    Args:
        event: Event containing deployment ID.
        traffic_service: Traffic service instance.
        deployment_service: Deployment service instance.
        monitoring_service: Monitoring service instance.
        notification_service: Notification service instance.

    Returns:
        Response with auto shift results.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    # Get deployment configuration
    deployment = deployment_service.get_deployment(deployment_id)
    endpoint_name = deployment["endpoint_name"]
    canary_variant = deployment["canary_variant"]["variant_name"]
    current_variant = deployment["current_variant"]["variant_name"]
    step_size = deployment.get("traffic_config", {}).get("step_size", 0.1)

    # Check canary health before shifting
    canary_metrics = monitoring_service.get_variant_metrics(
        endpoint_name=endpoint_name,
        variant_name=canary_variant,
    )

    # Evaluate health
    latency_threshold = deployment.get("latency_threshold_ms", 100.0)
    error_rate_threshold = deployment.get("error_rate_threshold", 0.01)

    if canary_metrics.model_latency_p99_ms > latency_threshold:
        logger.warning(
            "Canary latency exceeds threshold, skipping auto-shift",
            deployment_id=deployment_id,
            latency=canary_metrics.model_latency_p99_ms,
            threshold=latency_threshold,
        )
        return {
            "statusCode": 200,
            "body": json_serialize({
                "deployment_id": deployment_id,
                "status": "skipped",
                "reason": "Canary latency exceeds threshold",
            }),
        }

    if canary_metrics.error_rate > error_rate_threshold:
        logger.warning(
            "Canary error rate exceeds threshold, skipping auto-shift",
            deployment_id=deployment_id,
            error_rate=canary_metrics.error_rate,
            threshold=error_rate_threshold,
        )
        return {
            "statusCode": 200,
            "body": json_serialize({
                "deployment_id": deployment_id,
                "status": "skipped",
                "reason": "Canary error rate exceeds threshold",
            }),
        }

    # Get current weights
    current_weights = traffic_service.get_variant_weights(endpoint_name)
    canary_weight = current_weights.get(canary_variant, 0.0)

    # Check if deployment is complete
    if canary_weight >= 1.0:
        logger.info(
            "Canary at 100%, deployment complete",
            deployment_id=deployment_id,
        )
        deployment_service.mark_deployment_complete(deployment_id)
        return {
            "statusCode": 200,
            "body": json_serialize({
                "deployment_id": deployment_id,
                "status": "completed",
                "message": "Canary promoted to 100%",
            }),
        }

    # Calculate new weights with step increase
    new_canary_weight = min(canary_weight + step_size, 1.0)
    new_production_weight = max(1.0 - new_canary_weight, 0.0)

    new_weights = {
        canary_variant: new_canary_weight,
        current_variant: new_production_weight,
    }

    logger.info(
        "Auto-shifting traffic",
        deployment_id=deployment_id,
        from_canary_weight=canary_weight,
        to_canary_weight=new_canary_weight,
    )

    # Execute traffic shift
    traffic_service.update_variant_weights(endpoint_name, new_weights)

    # Record event
    shift_event = TrafficShiftEvent(
        deployment_id=deployment_id,
        event_id=generate_event_id(),
        from_weights=current_weights,
        to_weights=new_weights,
        reason=f"Auto shift: canary healthy, increasing by {step_size}",
        triggered_by="auto_shift_scheduler",
    )
    deployment_service.record_event(shift_event)

    notification_service.send_traffic_shift_notification(shift_event)

    return {
        "statusCode": 200,
        "body": json_serialize({
            "deployment_id": deployment_id,
            "endpoint_name": endpoint_name,
            "previous_weights": current_weights,
            "new_weights": new_weights,
            "status": "shifted",
        }),
    }


def _handle_get_weights(
    event: dict[str, Any],
    traffic_service: TrafficService,
) -> dict[str, Any]:
    """Get current variant weights for an endpoint.

    Args:
        event: Event containing endpoint name.
        traffic_service: Traffic service instance.

    Returns:
        Response with current weights.
    """
    endpoint_name = event.get("endpoint_name")
    if not endpoint_name:
        raise ValidationError("endpoint_name is required")

    weights = traffic_service.get_variant_weights(endpoint_name)

    return {
        "statusCode": 200,
        "body": json_serialize({
            "endpoint_name": endpoint_name,
            "weights": weights,
        }),
    }


def _handle_set_weights(
    event: dict[str, Any],
    traffic_service: TrafficService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Set variant weights directly.

    Args:
        event: Event containing endpoint name and weights.
        traffic_service: Traffic service instance.
        notification_service: Notification service instance.

    Returns:
        Response with update status.
    """
    endpoint_name = event.get("endpoint_name")
    if not endpoint_name:
        raise ValidationError("endpoint_name is required")

    weights = event.get("weights")
    if not weights:
        raise ValidationError("weights dictionary is required")

    # Normalize and validate weights
    weights = normalize_weights(weights)

    logger.info(
        "Setting variant weights directly",
        endpoint_name=endpoint_name,
        weights=weights,
    )

    result = traffic_service.update_variant_weights(endpoint_name, weights)

    return {
        "statusCode": 200,
        "body": json_serialize({
            "endpoint_name": endpoint_name,
            "weights": weights,
            "status": "updated",
        }),
    }
