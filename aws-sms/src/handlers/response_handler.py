"""SMS Response Handler Lambda.

Processes inbound SMS responses, stores them in DynamoDB,
and handles opt-in/opt-out requests.
"""

import hashlib
from datetime import datetime, timedelta
from typing import Any

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from services.kinesis_service import KinesisService
from services.pinpoint_service import PinpointService
from services.analytics_service import AnalyticsService
from common.clients import get_dynamodb_client, get_sns_client
from common.config import settings
from common.models import InboundSMS, SMSResponse, SubscriptionStatus

logger = Logger()
tracer = Tracer()
metrics = Metrics()

kinesis_service = KinesisService()
pinpoint_service = PinpointService()
analytics_service = AnalyticsService()
dynamodb = get_dynamodb_client()
sns = get_sns_client()


def generate_subscriber_id(phone_number: str) -> str:
    """Generate a consistent subscriber ID from phone number."""
    return hashlib.sha256(phone_number.encode()).hexdigest()[:16]


@tracer.capture_method
def store_response(inbound: InboundSMS) -> SMSResponse:
    """Store the SMS response in DynamoDB."""
    subscriber_id = generate_subscriber_id(inbound.origination_number)
    now = datetime.utcnow()
    ttl = int((now + timedelta(days=settings.ttl_days)).timestamp())

    response = SMSResponse(
        subscriber_id=subscriber_id,
        response_timestamp=now.isoformat(),
        phone_number=inbound.origination_number,
        response_text=inbound.message_body,
        normalized_response=inbound.get_normalized_response(),
        campaign_id="",  # Could be extracted from context if available
        journey_id="",
        response_date=now.strftime("%Y-%m-%d"),
        sentiment=analytics_service.analyze_response_sentiment(inbound.message_body),
        is_opt_out=inbound.is_opt_out(),
        is_confirmation=inbound.is_confirmation(),
        ttl=ttl,
    )

    dynamodb.put_item(
        TableName=settings.responses_table,
        Item=response.to_dynamodb_item(),
    )

    logger.info(
        "Stored SMS response",
        extra={
            "subscriber_id": subscriber_id,
            "sentiment": response.sentiment,
            "is_opt_out": response.is_opt_out,
            "is_confirmation": response.is_confirmation,
        },
    )

    return response


@tracer.capture_method
def update_subscriber_status(
    subscriber_id: str,
    phone_number: str,
    status: SubscriptionStatus,
) -> None:
    """Update subscriber status in DynamoDB."""
    now = datetime.utcnow()

    update_expression = "SET subscription_status = :status, updated_at = :updated"
    expression_values = {
        ":status": {"S": status.value},
        ":updated": {"S": now.isoformat()},
    }

    if status == SubscriptionStatus.OPTED_OUT:
        update_expression += ", opt_out_timestamp = :opt_out"
        expression_values[":opt_out"] = {"S": now.isoformat()}
    elif status == SubscriptionStatus.ACTIVE:
        update_expression += ", opt_in_timestamp = :opt_in"
        expression_values[":opt_in"] = {"S": now.isoformat()}

    dynamodb.update_item(
        TableName=settings.subscribers_table,
        Key={"subscriber_id": {"S": subscriber_id}},
        UpdateExpression=update_expression,
        ExpressionAttributeValues=expression_values,
    )

    logger.info(
        "Updated subscriber status",
        extra={
            "subscriber_id": subscriber_id,
            "status": status.value,
        },
    )


@tracer.capture_method
def handle_opt_out(inbound: InboundSMS) -> None:
    """Handle opt-out request."""
    subscriber_id = generate_subscriber_id(inbound.origination_number)

    # Update Pinpoint endpoint
    try:
        pinpoint_service.opt_out_endpoint(
            endpoint_id=subscriber_id,
            phone_number=inbound.origination_number,
        )
    except Exception as e:
        logger.warning(f"Failed to update Pinpoint endpoint: {e}")

    # Update subscriber table
    update_subscriber_status(
        subscriber_id=subscriber_id,
        phone_number=inbound.origination_number,
        status=SubscriptionStatus.OPTED_OUT,
    )

    # Send confirmation
    try:
        pinpoint_service.send_opt_out_confirmation(inbound.origination_number)
    except Exception as e:
        logger.warning(f"Failed to send opt-out confirmation: {e}")

    # Publish notification
    if settings.notifications_topic:
        sns.publish(
            TopicArn=settings.notifications_topic,
            Subject="SMS Opt-Out",
            Message=f"Subscriber {subscriber_id} has opted out.",
        )

    metrics.add_metric(name="OptOutProcessed", unit=MetricUnit.Count, value=1)


@tracer.capture_method
def handle_confirmation(inbound: InboundSMS) -> None:
    """Handle confirmation response."""
    subscriber_id = generate_subscriber_id(inbound.origination_number)

    # Update Pinpoint endpoint
    try:
        pinpoint_service.opt_in_endpoint(
            endpoint_id=subscriber_id,
            phone_number=inbound.origination_number,
        )
    except Exception as e:
        logger.warning(f"Failed to update Pinpoint endpoint: {e}")

    # Update subscriber table
    update_subscriber_status(
        subscriber_id=subscriber_id,
        phone_number=inbound.origination_number,
        status=SubscriptionStatus.ACTIVE,
    )

    # Send confirmation
    try:
        pinpoint_service.send_confirmation_response(inbound.origination_number)
    except Exception as e:
        logger.warning(f"Failed to send confirmation response: {e}")

    metrics.add_metric(name="ConfirmationProcessed", unit=MetricUnit.Count, value=1)


@tracer.capture_method
def process_inbound_sms(inbound: InboundSMS) -> dict:
    """Process a single inbound SMS."""
    # Store the response
    response = store_response(inbound)

    # Handle special responses
    if inbound.is_opt_out():
        handle_opt_out(inbound)
        return {"action": "opt_out", "subscriber_id": response.subscriber_id}
    elif inbound.is_confirmation():
        handle_confirmation(inbound)
        return {"action": "confirmation", "subscriber_id": response.subscriber_id}
    else:
        # Regular response - could trigger targeted promotions
        metrics.add_metric(name="RegularResponse", unit=MetricUnit.Count, value=1)
        return {"action": "stored", "subscriber_id": response.subscriber_id}


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for SMS response processing."""
    kinesis_event = KinesisStreamEvent(event)

    logger.info(
        "Processing SMS responses",
        extra={"record_count": len(kinesis_event.records)},
    )

    processed = 0
    failed = 0
    results = []

    for record in kinesis_event.records:
        try:
            data = kinesis_service.decode_record({"kinesis": record.raw_event["kinesis"]})
            inbound = kinesis_service.parse_inbound_sms(data)

            if not inbound:
                continue

            result = process_inbound_sms(inbound)
            results.append(result)
            processed += 1

        except Exception as e:
            logger.error(f"Failed to process response: {e}")
            failed += 1

    logger.info(
        "Completed response processing",
        extra={
            "processed": processed,
            "failed": failed,
        },
    )

    return {
        "statusCode": 200,
        "body": {
            "processed": processed,
            "failed": failed,
            "results": results,
        },
    }
