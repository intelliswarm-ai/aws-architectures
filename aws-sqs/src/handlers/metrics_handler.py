"""Metrics handler for publishing custom CloudWatch metrics."""

from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from ..common.clients import get_autoscaling_client, get_cloudwatch_client
from ..common.config import settings
from ..common.models import QueueMetrics, ScalingDecision
from ..services.queue_service import QueueService

logger = Logger(service=settings.service_name)
tracer = Tracer(service=settings.service_name)

# Configuration
ASG_NAME = "banking-transaction-processors"
TARGET_MESSAGES_PER_INSTANCE = 100
MIN_INSTANCES = 2
MAX_INSTANCES = 10


@tracer.capture_method
def get_asg_instance_count() -> int:
    """Get current number of running instances in ASG."""
    client = get_autoscaling_client()
    try:
        response = client.describe_auto_scaling_groups(
            AutoScalingGroupNames=[ASG_NAME]
        )
        groups = response.get("AutoScalingGroups", [])
        if groups:
            # Count only InService instances
            instances = groups[0].get("Instances", [])
            running = sum(
                1 for i in instances
                if i.get("LifecycleState") == "InService"
            )
            return max(running, 1)  # Avoid division by zero
        return 1
    except Exception as e:
        logger.warning(
            "Failed to get ASG instance count",
            extra={"error": str(e)},
        )
        return 1


@tracer.capture_method
def calculate_backlog_per_instance(
    queue_metrics: QueueMetrics,
    instance_count: int,
) -> float:
    """Calculate the backlog per instance metric.

    This is the key metric used for SQS-based auto scaling.

    Args:
        queue_metrics: Current queue metrics.
        instance_count: Number of running instances.

    Returns:
        Messages per instance ratio.
    """
    return queue_metrics.approximate_messages / instance_count


@tracer.capture_method
def determine_scaling_action(
    queue_metrics: QueueMetrics,
    instance_count: int,
) -> ScalingDecision:
    """Determine if scaling is needed.

    Args:
        queue_metrics: Current queue metrics.
        instance_count: Current instance count.

    Returns:
        ScalingDecision with action and reasoning.
    """
    messages_per_instance = calculate_backlog_per_instance(
        queue_metrics,
        instance_count,
    )

    if messages_per_instance > TARGET_MESSAGES_PER_INSTANCE:
        # Calculate desired instances
        desired = min(
            MAX_INSTANCES,
            int(
                queue_metrics.approximate_messages
                / TARGET_MESSAGES_PER_INSTANCE
            ) + 1,
        )
        if desired > instance_count:
            return ScalingDecision(
                current_instances=instance_count,
                desired_instances=desired,
                queue_depth=queue_metrics.approximate_messages,
                messages_per_instance=messages_per_instance,
                action="scale_out",
                reason=(
                    f"Queue depth {queue_metrics.approximate_messages} "
                    f"exceeds target of {TARGET_MESSAGES_PER_INSTANCE} "
                    f"per instance"
                ),
            )

    if messages_per_instance < TARGET_MESSAGES_PER_INSTANCE * 0.5:
        # Scale in if significantly below target
        desired = max(
            MIN_INSTANCES,
            int(
                queue_metrics.approximate_messages
                / TARGET_MESSAGES_PER_INSTANCE
            ) + 1,
        )
        if desired < instance_count:
            return ScalingDecision(
                current_instances=instance_count,
                desired_instances=desired,
                queue_depth=queue_metrics.approximate_messages,
                messages_per_instance=messages_per_instance,
                action="scale_in",
                reason=(
                    f"Queue depth {queue_metrics.approximate_messages} "
                    f"is below 50% of target capacity"
                ),
            )

    return ScalingDecision(
        current_instances=instance_count,
        desired_instances=instance_count,
        queue_depth=queue_metrics.approximate_messages,
        messages_per_instance=messages_per_instance,
        action="no_change",
        reason="Queue depth within target range",
    )


@tracer.capture_method
def publish_custom_metrics(
    queue_metrics: QueueMetrics,
    instance_count: int,
    scaling_decision: ScalingDecision,
) -> None:
    """Publish custom CloudWatch metrics.

    Publishes:
    - BacklogPerInstance: Key metric for scaling policies
    - QueueDepth: Total messages in queue
    - InFlightMessages: Messages being processed
    - ProcessorCount: Running EC2 instances

    Args:
        queue_metrics: Queue metrics.
        instance_count: Instance count.
        scaling_decision: Scaling decision.
    """
    client = get_cloudwatch_client()
    timestamp = datetime.utcnow()

    metrics_data = [
        {
            "MetricName": "BacklogPerInstance",
            "Dimensions": [
                {"Name": "QueueName", "Value": "transaction-queue"},
                {"Name": "AutoScalingGroupName", "Value": ASG_NAME},
            ],
            "Timestamp": timestamp,
            "Value": scaling_decision.messages_per_instance,
            "Unit": "Count",
        },
        {
            "MetricName": "QueueDepth",
            "Dimensions": [
                {"Name": "QueueName", "Value": "transaction-queue"},
            ],
            "Timestamp": timestamp,
            "Value": queue_metrics.approximate_messages,
            "Unit": "Count",
        },
        {
            "MetricName": "InFlightMessages",
            "Dimensions": [
                {"Name": "QueueName", "Value": "transaction-queue"},
            ],
            "Timestamp": timestamp,
            "Value": queue_metrics.approximate_messages_not_visible,
            "Unit": "Count",
        },
        {
            "MetricName": "ProcessorCount",
            "Dimensions": [
                {"Name": "AutoScalingGroupName", "Value": ASG_NAME},
            ],
            "Timestamp": timestamp,
            "Value": instance_count,
            "Unit": "Count",
        },
    ]

    try:
        client.put_metric_data(
            Namespace="BankingPlatform/SQS",
            MetricData=metrics_data,
        )
        logger.info(
            "Custom metrics published",
            extra={
                "backlog_per_instance": scaling_decision.messages_per_instance,
                "queue_depth": queue_metrics.approximate_messages,
                "instance_count": instance_count,
            },
        )
    except Exception as e:
        logger.error(
            "Failed to publish metrics",
            extra={"error": str(e)},
        )
        raise


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda handler for metrics collection.

    Triggered by EventBridge schedule (every 1 minute).

    Args:
        event: EventBridge scheduled event.
        context: Lambda context.

    Returns:
        Processing result with metrics summary.
    """
    logger.info("Collecting metrics")

    # Get queue metrics
    queue_service = QueueService()
    queue_metrics = queue_service.get_queue_metrics()

    # Get ASG instance count
    instance_count = get_asg_instance_count()

    # Determine scaling action
    scaling_decision = determine_scaling_action(queue_metrics, instance_count)

    # Publish custom metrics
    publish_custom_metrics(queue_metrics, instance_count, scaling_decision)

    # Log scaling decision
    if scaling_decision.action != "no_change":
        logger.info(
            "Scaling recommendation",
            extra={
                "action": scaling_decision.action,
                "current": scaling_decision.current_instances,
                "desired": scaling_decision.desired_instances,
                "reason": scaling_decision.reason,
            },
        )

    return {
        "statusCode": 200,
        "body": {
            "queue_depth": queue_metrics.approximate_messages,
            "instance_count": instance_count,
            "backlog_per_instance": scaling_decision.messages_per_instance,
            "scaling_action": scaling_decision.action,
            "scaling_reason": scaling_decision.reason,
        },
    }
