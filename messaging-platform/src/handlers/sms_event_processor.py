"""SMS Event Processor Lambda Handler.

Processes all SMS events from Pinpoint via Kinesis for monitoring and logging.
"""

from typing import Any

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from services.kinesis_service import KinesisService
from services.analytics_service import AnalyticsService
from common.models import SMSEventType

logger = Logger()
tracer = Tracer()
metrics = Metrics()
processor = BatchProcessor(event_type=EventType.KinesisDataStreams)


kinesis_service = KinesisService()
analytics_service = AnalyticsService()


@tracer.capture_method
def process_record(record: dict) -> dict:
    """Process a single Kinesis record."""
    try:
        data = kinesis_service.decode_record({"kinesis": record})
        sms_event = kinesis_service.parse_sms_event(data)

        if not sms_event:
            logger.debug("Skipping non-SMS event")
            return {"status": "skipped"}

        # Log event for monitoring
        logger.info(
            "Processed SMS event",
            extra={
                "event_type": sms_event.event_type,
                "message_id": sms_event.message_id,
                "record_status": sms_event.record_status,
                "campaign_id": sms_event.campaign_id,
            },
        )

        # Track metrics
        if sms_event.event_type == SMSEventType.SUCCESS.value:
            metrics.add_metric(
                name="DeliverySuccess",
                unit=MetricUnit.Count,
                value=1,
            )
        elif sms_event.event_type == SMSEventType.FAILURE.value:
            metrics.add_metric(
                name="DeliveryFailed",
                unit=MetricUnit.Count,
                value=1,
            )
        elif sms_event.event_type == SMSEventType.OPTOUT.value:
            metrics.add_metric(
                name="OptOut",
                unit=MetricUnit.Count,
                value=1,
            )
        elif sms_event.event_type == SMSEventType.RECEIVED.value:
            metrics.add_metric(
                name="ResponseReceived",
                unit=MetricUnit.Count,
                value=1,
            )

        return {"status": "processed", "event_type": sms_event.event_type}

    except Exception as e:
        logger.error(f"Failed to process record: {e}")
        raise


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for SMS event processing."""
    kinesis_event = KinesisStreamEvent(event)

    logger.info(
        "Processing SMS events batch",
        extra={"record_count": len(kinesis_event.records)},
    )

    # Collect all events for batch analytics
    all_events = []
    for record in kinesis_event.records:
        try:
            data = kinesis_service.decode_record({"kinesis": record.raw_event["kinesis"]})
            sms_event = kinesis_service.parse_sms_event(data)
            if sms_event:
                all_events.append(sms_event)
        except Exception as e:
            logger.warning(f"Failed to parse event for analytics: {e}")

    # Publish batch analytics
    if all_events:
        batch_metrics = analytics_service.calculate_metrics(all_events)
        analytics_service.publish_metrics(batch_metrics)

        # Group by campaign and publish campaign-specific metrics
        campaign_events: dict = {}
        for event in all_events:
            if event.campaign_id:
                if event.campaign_id not in campaign_events:
                    campaign_events[event.campaign_id] = []
                campaign_events[event.campaign_id].append(event)

        for campaign_id, events in campaign_events.items():
            analytics_service.publish_campaign_metrics(campaign_id, events)

    return {
        "statusCode": 200,
        "body": {
            "processed": len(all_events),
            "total_records": len(kinesis_event.records),
        },
    }
