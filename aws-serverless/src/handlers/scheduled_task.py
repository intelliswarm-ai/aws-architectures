"""Scheduled Task Handler for Periodic Jobs.

This handler processes EventBridge scheduled events for maintenance tasks,
health checks, and report generation.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_aws_clients
from src.common.config import get_settings
from src.common.utils import json_dumps, utc_now

logger = Logger()
tracer = Tracer()
metrics = Metrics()

settings = get_settings()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Scheduled task handler.

    Routes to specific task based on EventBridge rule source or detail-type.

    Args:
        event: EventBridge scheduled event
        context: Lambda context

    Returns:
        Task execution result
    """
    # Determine which task to run
    detail_type = event.get("detail-type", "")
    source = event.get("source", "")
    detail = event.get("detail", {})
    task_type = detail.get("task_type", "")

    # Support direct invocation with task type
    if not task_type and detail_type:
        task_type = detail_type.lower().replace(" ", "_")

    logger.info(f"Executing scheduled task: {task_type}")

    try:
        result = route_task(task_type, detail)

        metrics.add_metric(name="ScheduledTasksCompleted", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="TaskType", value=task_type)

        return {
            "status": "success",
            "task_type": task_type,
            "result": result,
        }

    except Exception as e:
        logger.exception(f"Scheduled task failed: {e}")
        metrics.add_metric(name="ScheduledTasksFailed", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="TaskType", value=task_type)

        return {
            "status": "failed",
            "task_type": task_type,
            "error": str(e),
        }


@tracer.capture_method
def route_task(task_type: str, detail: dict[str, Any]) -> Any:
    """Route to appropriate task handler.

    Args:
        task_type: Type of scheduled task
        detail: Task details/parameters

    Returns:
        Task result
    """
    tasks = {
        "health_check": run_health_check,
        "cleanup_expired": cleanup_expired_items,
        "generate_report": generate_daily_report,
        "sync_data": sync_external_data,
        "rotate_logs": rotate_log_retention,
        "warm_cache": warm_cache,
        "check_quotas": check_service_quotas,
    }

    task_func = tasks.get(task_type)
    if not task_func:
        logger.warning(f"Unknown task type: {task_type}")
        return {"status": "unknown_task"}

    return task_func(detail)


@tracer.capture_method
def run_health_check(detail: dict[str, Any]) -> dict[str, Any]:
    """Run system health checks.

    Checks connectivity to critical services and reports status.
    """
    logger.info("Running health check")
    results: dict[str, Any] = {
        "timestamp": utc_now().isoformat(),
        "checks": {},
    }

    clients = get_aws_clients()

    # Check DynamoDB
    try:
        if settings.tenant_table:
            clients.dynamodb.describe_table(TableName=settings.tenant_table)
            results["checks"]["dynamodb"] = "healthy"
        else:
            results["checks"]["dynamodb"] = "not_configured"
    except Exception as e:
        results["checks"]["dynamodb"] = f"unhealthy: {e}"

    # Check SQS
    try:
        if settings.processing_queue_url:
            clients.sqs.get_queue_attributes(
                QueueUrl=settings.processing_queue_url,
                AttributeNames=["ApproximateNumberOfMessages"],
            )
            results["checks"]["sqs"] = "healthy"
        else:
            results["checks"]["sqs"] = "not_configured"
    except Exception as e:
        results["checks"]["sqs"] = f"unhealthy: {e}"

    # Check Secrets Manager
    try:
        if settings.db_secret_arn:
            clients.secrets_manager.describe_secret(SecretId=settings.db_secret_arn)
            results["checks"]["secrets_manager"] = "healthy"
        else:
            results["checks"]["secrets_manager"] = "not_configured"
    except Exception as e:
        results["checks"]["secrets_manager"] = f"unhealthy: {e}"

    # Calculate overall health
    unhealthy = [k for k, v in results["checks"].items() if "unhealthy" in str(v)]
    results["overall"] = "healthy" if not unhealthy else "degraded"
    results["unhealthy_services"] = unhealthy

    if unhealthy:
        logger.warning(f"Health check found issues: {unhealthy}")
        # Send alert if configured
        if settings.alert_topic_arn:
            clients.sns.publish(
                TopicArn=settings.alert_topic_arn,
                Subject="Health Check Alert",
                Message=json_dumps(results),
            )

    return results


@tracer.capture_method
def cleanup_expired_items(detail: dict[str, Any]) -> dict[str, Any]:
    """Clean up expired items from DynamoDB.

    Removes items with expired TTL that weren't automatically deleted.
    """
    logger.info("Running cleanup of expired items")

    if not settings.tenant_table:
        return {"status": "skipped", "reason": "no_table_configured"}

    clients = get_aws_clients()
    table = clients.dynamodb_resource.Table(settings.tenant_table)

    # Query for items with TTL in the past
    now = int(utc_now().timestamp())
    cutoff = now - (24 * 60 * 60)  # Items expired more than 24 hours ago

    # Scan for expired items (in production, use a GSI on TTL)
    deleted_count = 0
    scanned_count = 0

    try:
        response = table.scan(
            FilterExpression="attribute_exists(#ttl) AND #ttl < :cutoff",
            ExpressionAttributeNames={"#ttl": "ttl"},
            ExpressionAttributeValues={":cutoff": cutoff},
            ProjectionExpression="PK, SK",
            Limit=1000,  # Process in batches
        )

        items = response.get("Items", [])
        scanned_count = response.get("ScannedCount", 0)

        # Delete expired items
        with table.batch_writer() as batch:
            for item in items:
                batch.delete_item(Key={"PK": item["PK"], "SK": item["SK"]})
                deleted_count += 1

    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        return {"status": "error", "error": str(e)}

    logger.info(f"Cleanup complete: deleted {deleted_count} of {scanned_count} items")

    return {
        "status": "success",
        "scanned": scanned_count,
        "deleted": deleted_count,
    }


@tracer.capture_method
def generate_daily_report(detail: dict[str, Any]) -> dict[str, Any]:
    """Generate daily usage/activity report.

    Aggregates metrics and stores report for review.
    """
    logger.info("Generating daily report")

    clients = get_aws_clients()
    end_time = utc_now()
    start_time = end_time - timedelta(days=1)

    report: dict[str, Any] = {
        "period_start": start_time.isoformat(),
        "period_end": end_time.isoformat(),
        "generated_at": utc_now().isoformat(),
        "metrics": {},
    }

    try:
        # Get Lambda invocation metrics
        response = clients.cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Invocations",
            Dimensions=[
                {"Name": "FunctionName", "Value": f"{settings.project_name}-api-handler"},
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=["Sum"],
        )

        datapoints = response.get("Datapoints", [])
        if datapoints:
            report["metrics"]["api_invocations"] = int(datapoints[0].get("Sum", 0))

        # Get error metrics
        response = clients.cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="Errors",
            Dimensions=[
                {"Name": "FunctionName", "Value": f"{settings.project_name}-api-handler"},
            ],
            StartTime=start_time,
            EndTime=end_time,
            Period=86400,
            Statistics=["Sum"],
        )

        datapoints = response.get("Datapoints", [])
        if datapoints:
            report["metrics"]["api_errors"] = int(datapoints[0].get("Sum", 0))

    except Exception as e:
        logger.warning(f"Failed to get CloudWatch metrics: {e}")

    # Store report in S3 (if configured) or DynamoDB
    if settings.audit_table:
        try:
            table = clients.dynamodb_resource.Table(settings.audit_table)
            table.put_item(
                Item={
                    "PK": f"REPORT#{end_time.strftime('%Y-%m-%d')}",
                    "SK": "daily",
                    **report,
                    "ttl": int((end_time + timedelta(days=90)).timestamp()),
                }
            )
        except Exception as e:
            logger.error(f"Failed to store report: {e}")

    return report


@tracer.capture_method
def sync_external_data(detail: dict[str, Any]) -> dict[str, Any]:
    """Sync data with external systems.

    Placeholder for integration with external data sources.
    """
    logger.info("Running external data sync")

    source = detail.get("source", "default")
    last_sync = detail.get("last_sync")

    # TODO: Implement actual sync logic based on source
    # - Fetch data from external API
    # - Transform and validate
    # - Store in DynamoDB

    return {
        "status": "success",
        "source": source,
        "records_synced": 0,
    }


@tracer.capture_method
def rotate_log_retention(detail: dict[str, Any]) -> dict[str, Any]:
    """Update log group retention policies.

    Ensures all log groups have appropriate retention periods.
    """
    logger.info("Checking log retention policies")

    clients = get_aws_clients()
    target_retention = 14 if settings.environment == "dev" else 90

    updated = 0
    checked = 0

    try:
        paginator = clients.logs.get_paginator("describe_log_groups")

        for page in paginator.paginate(logGroupNamePrefix=f"/aws/lambda/{settings.project_name}"):
            for log_group in page.get("logGroups", []):
                checked += 1
                current_retention = log_group.get("retentionInDays")

                if current_retention != target_retention:
                    clients.logs.put_retention_policy(
                        logGroupName=log_group["logGroupName"],
                        retentionInDays=target_retention,
                    )
                    updated += 1
                    logger.info(
                        f"Updated retention for {log_group['logGroupName']}: "
                        f"{current_retention} -> {target_retention}"
                    )

    except Exception as e:
        logger.error(f"Failed to update log retention: {e}")

    return {
        "status": "success",
        "checked": checked,
        "updated": updated,
        "target_retention_days": target_retention,
    }


@tracer.capture_method
def warm_cache(detail: dict[str, Any]) -> dict[str, Any]:
    """Warm caches with frequently accessed data.

    Pre-populates caches to improve response times.
    """
    logger.info("Warming caches")

    # TODO: Implement cache warming logic
    # - Load frequently accessed tenant configurations
    # - Pre-compute common aggregations
    # - Refresh external service tokens

    return {
        "status": "success",
        "items_cached": 0,
    }


@tracer.capture_method
def check_service_quotas(detail: dict[str, Any]) -> dict[str, Any]:
    """Check AWS service quotas and alert if approaching limits.

    Monitors Lambda concurrency, DynamoDB capacity, etc.
    """
    logger.info("Checking service quotas")

    clients = get_aws_clients()
    warnings: list[str] = []

    try:
        # Check Lambda concurrent executions
        response = clients.cloudwatch.get_metric_statistics(
            Namespace="AWS/Lambda",
            MetricName="ConcurrentExecutions",
            StartTime=utc_now() - timedelta(hours=1),
            EndTime=utc_now(),
            Period=300,
            Statistics=["Maximum"],
        )

        datapoints = response.get("Datapoints", [])
        if datapoints:
            max_concurrent = max(dp.get("Maximum", 0) for dp in datapoints)
            # Default Lambda quota is 1000
            if max_concurrent > 800:
                warnings.append(f"Lambda concurrency at {max_concurrent}/1000")

    except Exception as e:
        logger.warning(f"Failed to check Lambda quotas: {e}")

    if warnings and settings.alert_topic_arn:
        clients.sns.publish(
            TopicArn=settings.alert_topic_arn,
            Subject="Service Quota Warning",
            Message=json_dumps({"warnings": warnings}),
        )

    return {
        "status": "success",
        "warnings": warnings,
    }
