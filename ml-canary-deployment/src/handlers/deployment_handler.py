"""Handler for managing canary deployments."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import DeploymentError, ValidationError
from src.common.models import (
    DeploymentConfig,
    DeploymentStatus,
    ModelVariant,
    TrafficConfig,
)
from src.common.utils import generate_deployment_id, json_deserialize, json_serialize
from src.services.deployment_service import DeploymentService
from src.services.notification_service import NotificationService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Handle deployment management requests.

    Supports creating new canary deployments, updating production variants,
    and managing deployment lifecycle.

    Args:
        event: Event containing deployment action and configuration.
        context: Lambda context object.

    Returns:
        Response with deployment status and details.
    """
    action = event.get("action", "create")
    logger.info("Processing deployment action", action=action)

    try:
        settings = get_settings()
        clients = get_clients()
        deployment_service = DeploymentService(clients, settings)
        notification_service = NotificationService(clients, settings)

        if action == "create":
            return _handle_create_deployment(event, deployment_service, notification_service)
        elif action == "update_variant":
            return _handle_update_variant(event, deployment_service)
        elif action == "get_status":
            return _handle_get_status(event, deployment_service)
        elif action == "complete":
            return _handle_complete_deployment(event, deployment_service, notification_service)
        elif action == "cancel":
            return _handle_cancel_deployment(event, deployment_service, notification_service)
        else:
            raise ValidationError(f"Unknown action: {action}")

    except ValidationError as e:
        logger.warning("Validation error", error=str(e))
        return {"statusCode": 400, "body": json_serialize({"error": e.message})}

    except DeploymentError as e:
        logger.error("Deployment error", error=str(e), details=e.details)
        return {"statusCode": 500, "body": json_serialize(e.to_dict())}

    except Exception as e:
        logger.exception("Unexpected error during deployment")
        return {"statusCode": 500, "body": json_serialize({"error": str(e)})}


def _handle_create_deployment(
    event: dict[str, Any],
    deployment_service: DeploymentService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Create a new canary deployment.

    Args:
        event: Event containing deployment configuration.
        deployment_service: Deployment service instance.
        notification_service: Notification service instance.

    Returns:
        Response with deployment details.
    """
    config = event.get("config", {})
    deployment_id = generate_deployment_id()

    # Validate and build configuration
    endpoint_name = config.get("endpoint_name")
    if not endpoint_name:
        raise ValidationError("endpoint_name is required")

    # Build current variant configuration
    current_variant_config = config.get("current_variant", {})
    current_variant = ModelVariant(
        variant_name=current_variant_config.get("variant_name", "production"),
        model_name=current_variant_config.get("model_name"),
        instance_type=current_variant_config.get("instance_type", "ml.m5.xlarge"),
        initial_instance_count=current_variant_config.get("initial_instance_count", 1),
        initial_weight=current_variant_config.get("initial_weight", 0.9),
    )

    # Build canary variant configuration
    canary_variant_config = config.get("canary_variant", {})
    if not canary_variant_config.get("model_name"):
        raise ValidationError("canary_variant.model_name is required")

    canary_variant = ModelVariant(
        variant_name=canary_variant_config.get("variant_name", "canary"),
        model_name=canary_variant_config.get("model_name"),
        instance_type=canary_variant_config.get("instance_type", "ml.m5.xlarge"),
        initial_instance_count=canary_variant_config.get("initial_instance_count", 1),
        initial_weight=canary_variant_config.get("initial_weight", 0.1),
    )

    # Build traffic configuration
    traffic_config = TrafficConfig(
        variant_weights={
            current_variant.variant_name: current_variant.initial_weight,
            canary_variant.variant_name: canary_variant.initial_weight,
        },
        canary_size=config.get("canary_size", 0.1),
        step_size=config.get("step_size", 0.1),
        bake_time_minutes=config.get("bake_time_minutes", 10),
    )

    # Create deployment configuration
    deployment_config = DeploymentConfig(
        deployment_id=deployment_id,
        endpoint_name=endpoint_name,
        current_variant=current_variant,
        canary_variant=canary_variant,
        traffic_config=traffic_config,
        auto_rollback_enabled=config.get("auto_rollback_enabled", True),
        latency_threshold_ms=config.get("latency_threshold_ms", 100.0),
        error_rate_threshold=config.get("error_rate_threshold", 0.01),
    )

    logger.info(
        "Creating canary deployment",
        deployment_id=deployment_id,
        endpoint_name=endpoint_name,
        canary_model=canary_variant.model_name,
    )

    # Create the deployment
    result = deployment_service.create_deployment(deployment_config)

    # Send notification
    notification_service.send_deployment_started(deployment_config)

    return {
        "statusCode": 201,
        "body": json_serialize({
            "deployment_id": deployment_id,
            "status": result["status"],
            "endpoint_name": endpoint_name,
            "message": "Canary deployment initiated",
        }),
    }


def _handle_update_variant(
    event: dict[str, Any],
    deployment_service: DeploymentService,
) -> dict[str, Any]:
    """Update an existing production variant.

    Args:
        event: Event containing variant update configuration.
        deployment_service: Deployment service instance.

    Returns:
        Response with update status.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    variant_config = event.get("variant_config", {})
    variant_name = variant_config.get("variant_name")
    if not variant_name:
        raise ValidationError("variant_name is required")

    result = deployment_service.update_variant(
        deployment_id=deployment_id,
        variant_name=variant_name,
        instance_count=variant_config.get("instance_count"),
        instance_type=variant_config.get("instance_type"),
    )

    return {
        "statusCode": 200,
        "body": json_serialize({
            "deployment_id": deployment_id,
            "variant_name": variant_name,
            "status": result["status"],
        }),
    }


def _handle_get_status(
    event: dict[str, Any],
    deployment_service: DeploymentService,
) -> dict[str, Any]:
    """Get deployment status.

    Args:
        event: Event containing deployment ID.
        deployment_service: Deployment service instance.

    Returns:
        Response with deployment status.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    status = deployment_service.get_deployment_status(deployment_id)

    return {
        "statusCode": 200,
        "body": json_serialize(status),
    }


def _handle_complete_deployment(
    event: dict[str, Any],
    deployment_service: DeploymentService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Complete a canary deployment by promoting canary to production.

    Args:
        event: Event containing deployment ID.
        deployment_service: Deployment service instance.
        notification_service: Notification service instance.

    Returns:
        Response with completion status.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    logger.info("Completing deployment", deployment_id=deployment_id)

    result = deployment_service.complete_deployment(deployment_id)

    notification_service.send_deployment_completed(
        deployment_id=deployment_id,
        endpoint_name=result["endpoint_name"],
    )

    return {
        "statusCode": 200,
        "body": json_serialize({
            "deployment_id": deployment_id,
            "status": DeploymentStatus.COMPLETED.value,
            "message": "Canary promoted to production",
        }),
    }


def _handle_cancel_deployment(
    event: dict[str, Any],
    deployment_service: DeploymentService,
    notification_service: NotificationService,
) -> dict[str, Any]:
    """Cancel a deployment and remove canary variant.

    Args:
        event: Event containing deployment ID.
        deployment_service: Deployment service instance.
        notification_service: Notification service instance.

    Returns:
        Response with cancellation status.
    """
    deployment_id = event.get("deployment_id")
    if not deployment_id:
        raise ValidationError("deployment_id is required")

    reason = event.get("reason", "Manual cancellation")

    logger.info("Cancelling deployment", deployment_id=deployment_id, reason=reason)

    result = deployment_service.cancel_deployment(deployment_id, reason)

    notification_service.send_deployment_cancelled(
        deployment_id=deployment_id,
        reason=reason,
    )

    return {
        "statusCode": 200,
        "body": json_serialize({
            "deployment_id": deployment_id,
            "status": "CANCELLED",
            "reason": reason,
        }),
    }
