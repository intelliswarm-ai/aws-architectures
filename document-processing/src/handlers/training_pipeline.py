"""Training pipeline handler - manages SageMaker training jobs."""

import time
import uuid
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.services.notification_service import NotificationService
from src.services.sagemaker_service import SageMakerService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Training pipeline handler.

    Can be triggered by EventBridge schedule or manual invocation.
    Manages the full training lifecycle: prepare, train, register, deploy.
    """
    action = event.get("action", "start_training")

    actions = {
        "start_training": start_training_handler,
        "check_status": check_status_handler,
        "register_model": register_model_handler,
        "deploy_model": deploy_model_handler,
    }

    handler_func = actions.get(action, start_training_handler)
    return handler_func(event, context)


def start_training_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Start a new SageMaker training job."""
    settings = get_settings()
    sagemaker_service = SageMakerService()

    # Generate job name
    timestamp = int(time.time())
    job_name = f"doc-classifier-{timestamp}-{uuid.uuid4().hex[:8]}"

    # Get training parameters from event or defaults
    training_data_uri = event.get(
        "training_data_uri",
        f"s3://{settings.model_bucket}/training-data/",
    )
    output_uri = event.get(
        "output_uri",
        f"s3://{settings.model_bucket}/model-artifacts/",
    )
    hyperparameters = event.get("hyperparameters", {
        "max_depth": "5",
        "eta": "0.2",
        "gamma": "4",
        "min_child_weight": "6",
        "subsample": "0.7",
        "objective": "multi:softmax",
        "num_class": "5",
        "num_round": "100",
    })

    logger.info(
        "Starting training job",
        job_name=job_name,
        training_data_uri=training_data_uri,
    )

    try:
        sagemaker_service.start_training_job(
            job_name=job_name,
            training_data_s3_uri=training_data_uri,
            output_s3_uri=output_uri,
            hyperparameters=hyperparameters,
            instance_type=settings.training_instance_type,
        )

        return {
            "status": "training_started",
            "job_name": job_name,
            "training_data_uri": training_data_uri,
            "output_uri": output_uri,
        }

    except Exception as e:
        logger.exception("Failed to start training job")
        raise


def check_status_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Check status of a training job."""
    job_name = event.get("job_name")

    if not job_name:
        raise ValueError("job_name is required")

    sagemaker_service = SageMakerService()
    notification_service = NotificationService()

    status = sagemaker_service.get_training_job_status(job_name)

    logger.info(
        "Training job status",
        job_name=job_name,
        status=status.get("status"),
        secondary_status=status.get("secondary_status"),
    )

    # Send notification if job completed or failed
    if status.get("status") == "Completed":
        notification_service.notify_training_complete(
            job_name=job_name,
            model_artifacts_uri=status.get("model_artifacts", ""),
            metrics={
                "training_time_seconds": status.get("training_time_seconds"),
                "billable_time_seconds": status.get("billable_time_seconds"),
            },
        )
    elif status.get("status") == "Failed":
        notification_service.notify_alert(
            alert_type="TrainingFailed",
            message=f"Training job {job_name} failed",
            details={
                "job_name": job_name,
                "failure_reason": status.get("failure_reason"),
            },
        )

    return {
        "job_name": job_name,
        **status,
    }


def register_model_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Register trained model in Model Registry."""
    job_name = event.get("job_name")
    model_artifacts_uri = event.get("model_artifacts_uri")

    if not job_name or not model_artifacts_uri:
        raise ValueError("job_name and model_artifacts_uri are required")

    settings = get_settings()
    sagemaker_service = SageMakerService()

    # Model package group name
    model_group_name = event.get("model_group_name", "document-classifier")

    # Model metrics from training (if available)
    model_metrics = event.get("model_metrics", {})

    logger.info(
        "Registering model",
        job_name=job_name,
        model_group_name=model_group_name,
    )

    try:
        model_package_arn = sagemaker_service.register_model(
            model_package_group_name=model_group_name,
            model_artifacts_s3_uri=model_artifacts_uri,
            model_metrics=model_metrics if model_metrics else None,
        )

        return {
            "status": "registered",
            "job_name": job_name,
            "model_package_arn": model_package_arn,
            "model_group_name": model_group_name,
        }

    except Exception as e:
        logger.exception("Failed to register model")
        raise


def deploy_model_handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Deploy model to SageMaker endpoint."""
    model_artifacts_uri = event.get("model_artifacts_uri")
    endpoint_name = event.get("endpoint_name")

    if not model_artifacts_uri:
        raise ValueError("model_artifacts_uri is required")

    settings = get_settings()
    sagemaker_service = SageMakerService()
    notification_service = NotificationService()

    # Use configured endpoint name or provided one
    endpoint_name = endpoint_name or settings.sagemaker_endpoint_name

    if not endpoint_name:
        raise ValueError("endpoint_name is required")

    timestamp = int(time.time())
    model_name = f"doc-classifier-{timestamp}"
    config_name = f"doc-classifier-config-{timestamp}"

    logger.info(
        "Deploying model",
        model_name=model_name,
        endpoint_name=endpoint_name,
    )

    try:
        # Create model
        sagemaker_service.create_model(
            model_name=model_name,
            model_artifacts_s3_uri=model_artifacts_uri,
        )

        # Create endpoint config
        sagemaker_service.create_endpoint_config(
            config_name=config_name,
            model_name=model_name,
            instance_type=settings.endpoint_instance_type,
        )

        # Update endpoint (blue/green deployment)
        sagemaker_service.update_endpoint(
            endpoint_name=endpoint_name,
            new_config_name=config_name,
        )

        notification_service.notify_alert(
            alert_type="ModelDeployed",
            message=f"New model deployed to endpoint {endpoint_name}",
            details={
                "model_name": model_name,
                "endpoint_name": endpoint_name,
                "config_name": config_name,
            },
        )

        return {
            "status": "deploying",
            "model_name": model_name,
            "endpoint_name": endpoint_name,
            "config_name": config_name,
        }

    except Exception as e:
        logger.exception("Failed to deploy model")
        notification_service.notify_alert(
            alert_type="DeploymentFailed",
            message=f"Failed to deploy model to {endpoint_name}",
            details={"error": str(e)},
        )
        raise
