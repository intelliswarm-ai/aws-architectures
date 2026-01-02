"""Analytics Processor Lambda Handler.

Processes SMS events for near-real-time analytics and CloudWatch metrics.
"""

from typing import Any
from collections import defaultdict

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from services.kinesis_service import KinesisService
from services.analytics_service import AnalyticsService
from common.models import SMSEvent, SMSEventType

logger = Logger()
tracer = Tracer()
metrics = Metrics()

kinesis_service = KinesisService()
analytics_service = AnalyticsService()


@tracer.capture_method
def aggregate_by_campaign(events: list[SMSEvent]) -> dict[str, list[SMSEvent]]:
    """Group events by campaign ID."""
    campaigns: dict[str, list[SMSEvent]] = defaultdict(list)

    for event in events:
        campaign_id = event.campaign_id or "no_campaign"
        campaigns[campaign_id].append(event)

    return dict(campaigns)


@tracer.capture_method
def aggregate_by_country(events: list[SMSEvent]) -> dict[str, dict]:
    """Aggregate metrics by country."""
    countries: dict[str, dict] = defaultdict(
        lambda: {"delivered": 0, "failed": 0, "cost": 0.0}
    )

    for event in events:
        country = event.iso_country_code or "unknown"

        if event.event_type == SMSEventType.SUCCESS.value:
            countries[country]["delivered"] += 1
        elif event.event_type == SMSEventType.FAILURE.value:
            countries[country]["failed"] += 1

        countries[country]["cost"] += event.price_millicents / 100000

    return dict(countries)


@tracer.capture_method
def publish_country_metrics(country_data: dict[str, dict]) -> None:
    """Publish country-specific metrics to CloudWatch."""
    cloudwatch = analytics_service.cloudwatch

    for country, data in country_data.items():
        if country == "unknown":
            continue

        metric_data = []

        if data["delivered"] > 0:
            metric_data.append({
                "MetricName": "MessagesDeliveredByCountry",
                "Value": data["delivered"],
                "Unit": "Count",
                "Dimensions": [{"Name": "Country", "Value": country}],
            })

        if data["failed"] > 0:
            metric_data.append({
                "MetricName": "MessagesFailedByCountry",
                "Value": data["failed"],
                "Unit": "Count",
                "Dimensions": [{"Name": "Country", "Value": country}],
            })

        if data["cost"] > 0:
            metric_data.append({
                "MetricName": "CostByCountry",
                "Value": data["cost"],
                "Unit": "None",
                "Dimensions": [{"Name": "Country", "Value": country}],
            })

        if metric_data:
            cloudwatch.put_metric_data(
                Namespace="SMS/Marketing",
                MetricData=metric_data,
            )


@tracer.capture_method
def calculate_delivery_stats(events: list[SMSEvent]) -> dict:
    """Calculate delivery statistics."""
    stats = {
        "total": 0,
        "delivered": 0,
        "failed": 0,
        "buffered": 0,
        "by_message_type": defaultdict(lambda: {"delivered": 0, "failed": 0}),
    }

    for event in events:
        message_type = event.message_type

        if event.event_type == SMSEventType.SUCCESS.value:
            stats["delivered"] += 1
            stats["by_message_type"][message_type]["delivered"] += 1
            stats["total"] += 1
        elif event.event_type == SMSEventType.FAILURE.value:
            stats["failed"] += 1
            stats["by_message_type"][message_type]["failed"] += 1
            stats["total"] += 1
        elif event.event_type == SMSEventType.BUFFERED.value:
            stats["buffered"] += 1
            stats["total"] += 1

    # Calculate rates
    if stats["total"] > 0:
        stats["delivery_rate"] = stats["delivered"] / stats["total"]
        stats["failure_rate"] = stats["failed"] / stats["total"]
    else:
        stats["delivery_rate"] = 0
        stats["failure_rate"] = 0

    return stats


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for analytics processing."""
    kinesis_event = KinesisStreamEvent(event)

    logger.info(
        "Processing events for analytics",
        extra={"record_count": len(kinesis_event.records)},
    )

    # Parse all events
    all_events: list[SMSEvent] = []
    for record in kinesis_event.records:
        try:
            data = kinesis_service.decode_record({"kinesis": record.raw_event["kinesis"]})
            sms_event = kinesis_service.parse_sms_event(data)
            if sms_event:
                all_events.append(sms_event)
        except Exception as e:
            logger.warning(f"Failed to parse event: {e}")

    if not all_events:
        logger.info("No SMS events to process")
        return {"statusCode": 200, "body": {"processed": 0}}

    # Calculate and publish overall metrics
    overall_metrics = analytics_service.calculate_metrics(all_events)
    analytics_service.publish_metrics(overall_metrics)

    # Calculate delivery stats
    delivery_stats = calculate_delivery_stats(all_events)

    # Log delivery stats
    metrics.add_metric(
        name="BatchDeliveryRate",
        unit=MetricUnit.Percent,
        value=delivery_stats["delivery_rate"] * 100,
    )

    # Aggregate by campaign
    campaign_events = aggregate_by_campaign(all_events)
    for campaign_id, events in campaign_events.items():
        if campaign_id != "no_campaign":
            analytics_service.publish_campaign_metrics(campaign_id, events)

    # Aggregate by country
    country_data = aggregate_by_country(all_events)
    publish_country_metrics(country_data)

    logger.info(
        "Completed analytics processing",
        extra={
            "total_events": len(all_events),
            "campaigns": len(campaign_events),
            "countries": len(country_data),
            "delivery_rate": delivery_stats["delivery_rate"],
        },
    )

    return {
        "statusCode": 200,
        "body": {
            "processed": len(all_events),
            "delivery_stats": {
                "delivered": delivery_stats["delivered"],
                "failed": delivery_stats["failed"],
                "delivery_rate": delivery_stats["delivery_rate"],
            },
            "campaigns": len(campaign_events),
            "countries": len(country_data),
        },
    }
