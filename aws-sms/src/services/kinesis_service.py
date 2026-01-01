"""Kinesis service for event processing."""

import base64
import json
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger

from common.clients import get_kinesis_client
from common.config import settings
from common.exceptions import KinesisError
from common.models import SMSEvent, InboundSMS

logger = Logger()


class KinesisService:
    """Service for Kinesis operations."""

    def __init__(self) -> None:
        self.client = get_kinesis_client()
        self.stream_name = settings.stream_name

    def decode_record(self, record: dict) -> dict:
        """Decode a Kinesis record from base64."""
        try:
            data = base64.b64decode(record["kinesis"]["data"])
            return json.loads(data)
        except (KeyError, json.JSONDecodeError) as e:
            raise KinesisError(
                f"Failed to decode Kinesis record: {e}",
                details={"record": str(record)[:200]},
            )

    def parse_sms_event(self, data: dict) -> SMSEvent | None:
        """Parse Kinesis record data into SMSEvent."""
        try:
            # Extract nested Pinpoint event structure
            event_type = data.get("event_type", "")
            if not event_type.startswith("_SMS"):
                return None

            attributes = data.get("attributes", {})
            metrics = data.get("metrics", {})
            application = data.get("application", {})
            client = data.get("client", {})

            return SMSEvent(
                event_type=event_type,
                event_timestamp=datetime.fromisoformat(
                    data.get("event_timestamp", datetime.utcnow().isoformat())
                ),
                arrival_timestamp=datetime.fromisoformat(
                    data.get("arrival_timestamp", datetime.utcnow().isoformat())
                ),
                app_id=application.get("app_id", ""),
                client_id=client.get("client_id", ""),
                message_id=attributes.get("message_id", ""),
                destination_phone=attributes.get("destination_phone_number", ""),
                origination_phone=attributes.get("origination_number", ""),
                record_status=attributes.get("record_status", ""),
                iso_country_code=attributes.get("iso_country_code", ""),
                message_type=attributes.get("message_type", "PROMOTIONAL"),
                price_millicents=metrics.get("price_in_millicents_usd", 0),
                campaign_id=attributes.get("campaign_id", ""),
                journey_id=attributes.get("journey_id", ""),
            )
        except Exception as e:
            logger.warning(f"Failed to parse SMS event: {e}", extra={"data": data})
            return None

    def parse_inbound_sms(self, data: dict) -> InboundSMS | None:
        """Parse Kinesis record data into InboundSMS."""
        try:
            event_type = data.get("event_type", "")
            if event_type != "_SMS.RECEIVED":
                return None

            attributes = data.get("attributes", {})

            return InboundSMS(
                event_timestamp=datetime.fromisoformat(
                    data.get("event_timestamp", datetime.utcnow().isoformat())
                ),
                origination_number=attributes.get("origination_number", ""),
                destination_number=attributes.get("destination_number", ""),
                message_body=attributes.get("message_body", ""),
                keyword=attributes.get("keyword", ""),
                message_id=attributes.get("message_id", ""),
            )
        except Exception as e:
            logger.warning(f"Failed to parse inbound SMS: {e}", extra={"data": data})
            return None

    def put_record(self, data: dict, partition_key: str) -> dict:
        """Put a record into the Kinesis stream."""
        try:
            response = self.client.put_record(
                StreamName=self.stream_name,
                Data=json.dumps(data).encode("utf-8"),
                PartitionKey=partition_key,
            )
            return response
        except Exception as e:
            raise KinesisError(
                f"Failed to put record to Kinesis: {e}",
                details={"partition_key": partition_key},
            )

    def process_records(
        self,
        records: list[dict],
    ) -> tuple[list[SMSEvent], list[InboundSMS], list[dict]]:
        """Process a batch of Kinesis records.

        Returns:
            Tuple of (sms_events, inbound_messages, failed_records)
        """
        sms_events = []
        inbound_messages = []
        failed_records = []

        for record in records:
            try:
                data = self.decode_record(record)

                # Try to parse as SMS event
                sms_event = self.parse_sms_event(data)
                if sms_event:
                    sms_events.append(sms_event)
                    continue

                # Try to parse as inbound SMS
                inbound = self.parse_inbound_sms(data)
                if inbound:
                    inbound_messages.append(inbound)
                    continue

            except KinesisError as e:
                logger.error(f"Failed to process record: {e}")
                failed_records.append(record)

        return sms_events, inbound_messages, failed_records
