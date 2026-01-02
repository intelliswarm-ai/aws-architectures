"""Integration tests for Kinesis service."""

import base64
import json
from datetime import datetime

import pytest
from moto import mock_aws

from services.kinesis_service import KinesisService
from common.models import SMSEvent


@mock_aws
class TestKinesisServiceIntegration:
    """Integration tests for KinesisService."""

    def test_decode_record_success(self, sample_sms_success_event):
        """Test successful record decoding."""
        service = KinesisService()

        # Create a Kinesis record format
        encoded_data = base64.b64encode(
            json.dumps(sample_sms_success_event).encode()
        ).decode()

        record = {"kinesis": {"data": encoded_data}}

        result = service.decode_record(record)

        assert result["event_type"] == "_SMS.SUCCESS"
        assert result["attributes"]["message_id"] == "msg-456"

    def test_parse_sms_event(self, sample_sms_success_event):
        """Test SMS event parsing."""
        service = KinesisService()

        event = service.parse_sms_event(sample_sms_success_event)

        assert event is not None
        assert event.event_type == "_SMS.SUCCESS"
        assert event.message_id == "msg-456"
        assert event.destination_phone == "+1234567890"
        assert event.record_status == "DELIVERED"
        assert event.campaign_id == "camp-001"

    def test_parse_inbound_sms(self, sample_inbound_sms_event):
        """Test inbound SMS parsing."""
        service = KinesisService()

        inbound = service.parse_inbound_sms(sample_inbound_sms_event)

        assert inbound is not None
        assert inbound.origination_number == "+1234567890"
        assert inbound.message_body == "YES"
        assert inbound.is_confirmation() is True

    def test_parse_opt_out(self, sample_opt_out_event):
        """Test opt-out event parsing."""
        service = KinesisService()

        inbound = service.parse_inbound_sms(sample_opt_out_event)

        assert inbound is not None
        assert inbound.message_body == "STOP"
        assert inbound.is_opt_out() is True

    def test_parse_non_sms_event(self):
        """Test that non-SMS events return None."""
        service = KinesisService()

        data = {"event_type": "_email.open", "attributes": {}}
        event = service.parse_sms_event(data)

        assert event is None

    def test_process_records_batch(
        self, sample_sms_success_event, sample_inbound_sms_event
    ):
        """Test batch record processing."""
        service = KinesisService()

        # Create mock Kinesis records
        records = [
            {
                "kinesis": {
                    "data": base64.b64encode(
                        json.dumps(sample_sms_success_event).encode()
                    ).decode()
                }
            },
            {
                "kinesis": {
                    "data": base64.b64encode(
                        json.dumps(sample_inbound_sms_event).encode()
                    ).decode()
                }
            },
        ]

        sms_events, inbound_messages, failed = service.process_records(records)

        assert len(sms_events) == 1
        assert len(inbound_messages) == 1
        assert len(failed) == 0
