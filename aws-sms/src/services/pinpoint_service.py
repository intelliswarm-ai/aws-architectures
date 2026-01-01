"""Pinpoint service for SMS operations."""

from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger

from common.clients import get_pinpoint_client
from common.config import settings
from common.exceptions import PinpointError
from common.models import SubscriptionStatus

logger = Logger()


class PinpointService:
    """Service for Pinpoint SMS operations."""

    def __init__(self) -> None:
        self.client = get_pinpoint_client()
        self.app_id = settings.pinpoint_app_id

    def update_endpoint(
        self,
        endpoint_id: str,
        phone_number: str,
        status: SubscriptionStatus,
        attributes: dict | None = None,
    ) -> dict:
        """Update an endpoint in Pinpoint."""
        try:
            endpoint_request = {
                "Address": phone_number,
                "ChannelType": "SMS",
                "OptOut": "ALL" if status == SubscriptionStatus.OPTED_OUT else "NONE",
                "Attributes": attributes or {},
                "User": {
                    "UserId": endpoint_id,
                },
            }

            response = self.client.update_endpoint(
                ApplicationId=self.app_id,
                EndpointId=endpoint_id,
                EndpointRequest=endpoint_request,
            )

            logger.info(
                "Updated Pinpoint endpoint",
                extra={
                    "endpoint_id": endpoint_id,
                    "status": status.value,
                },
            )
            return response

        except Exception as e:
            raise PinpointError(
                f"Failed to update Pinpoint endpoint: {e}",
                details={"endpoint_id": endpoint_id},
            )

    def get_endpoint(self, endpoint_id: str) -> dict | None:
        """Get an endpoint from Pinpoint."""
        try:
            response = self.client.get_endpoint(
                ApplicationId=self.app_id,
                EndpointId=endpoint_id,
            )
            return response.get("EndpointResponse", {})
        except self.client.exceptions.NotFoundException:
            return None
        except Exception as e:
            raise PinpointError(
                f"Failed to get Pinpoint endpoint: {e}",
                details={"endpoint_id": endpoint_id},
            )

    def send_sms(
        self,
        phone_number: str,
        message: str,
        message_type: str = "PROMOTIONAL",
        sender_id: str | None = None,
    ) -> dict:
        """Send an SMS message via Pinpoint."""
        try:
            message_request = {
                "Addresses": {
                    phone_number: {
                        "ChannelType": "SMS",
                    }
                },
                "MessageConfiguration": {
                    "SMSMessage": {
                        "Body": message,
                        "MessageType": message_type,
                    }
                },
            }

            if sender_id:
                message_request["MessageConfiguration"]["SMSMessage"]["SenderId"] = sender_id

            response = self.client.send_messages(
                ApplicationId=self.app_id,
                MessageRequest=message_request,
            )

            logger.info(
                "Sent SMS message",
                extra={
                    "phone_number": phone_number[:6] + "****",
                    "message_type": message_type,
                },
            )
            return response

        except Exception as e:
            raise PinpointError(
                f"Failed to send SMS: {e}",
                details={"phone_number": phone_number[:6] + "****"},
            )

    def opt_out_endpoint(self, endpoint_id: str, phone_number: str) -> dict:
        """Opt out an endpoint from SMS communications."""
        return self.update_endpoint(
            endpoint_id=endpoint_id,
            phone_number=phone_number,
            status=SubscriptionStatus.OPTED_OUT,
            attributes={
                "opt_out_timestamp": datetime.utcnow().isoformat(),
            },
        )

    def opt_in_endpoint(self, endpoint_id: str, phone_number: str) -> dict:
        """Opt in an endpoint for SMS communications."""
        return self.update_endpoint(
            endpoint_id=endpoint_id,
            phone_number=phone_number,
            status=SubscriptionStatus.ACTIVE,
            attributes={
                "opt_in_timestamp": datetime.utcnow().isoformat(),
            },
        )

    def send_confirmation_response(self, phone_number: str) -> dict:
        """Send a confirmation response SMS."""
        message = "Thank you for confirming! You're now subscribed to our updates."
        return self.send_sms(
            phone_number=phone_number,
            message=message,
            message_type="TRANSACTIONAL",
        )

    def send_opt_out_confirmation(self, phone_number: str) -> dict:
        """Send an opt-out confirmation SMS."""
        message = "You have been unsubscribed. Reply START to subscribe again."
        return self.send_sms(
            phone_number=phone_number,
            message=message,
            message_type="TRANSACTIONAL",
        )
