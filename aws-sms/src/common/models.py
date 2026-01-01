"""Data models for the SMS Marketing System."""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SMSEventType(str, Enum):
    """SMS event types from Pinpoint."""

    SUCCESS = "_SMS.SUCCESS"
    FAILURE = "_SMS.FAILURE"
    OPTOUT = "_SMS.OPTOUT"
    RECEIVED = "_SMS.RECEIVED"
    BUFFERED = "_SMS.BUFFERED"


class MessageType(str, Enum):
    """SMS message type."""

    PROMOTIONAL = "PROMOTIONAL"
    TRANSACTIONAL = "TRANSACTIONAL"


class SubscriptionStatus(str, Enum):
    """Subscriber status."""

    ACTIVE = "active"
    OPTED_OUT = "opted_out"
    PENDING = "pending"
    BOUNCED = "bounced"


class SMSEvent(BaseModel):
    """SMS event from Pinpoint via Kinesis."""

    event_type: str = Field(..., description="Type of SMS event")
    event_timestamp: datetime = Field(..., description="When the event occurred")
    arrival_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the event arrived in Kinesis",
    )
    application_id: str = Field(..., alias="app_id", description="Pinpoint app ID")
    client_id: str = Field(default="", description="Client/endpoint ID")
    message_id: str = Field(default="", description="Unique message ID")
    destination_phone: str = Field(default="", description="Destination phone number")
    origination_phone: str = Field(default="", description="Origination phone number")
    record_status: str = Field(default="", description="Delivery status")
    iso_country_code: str = Field(default="", description="Country code")
    message_type: str = Field(default="PROMOTIONAL", description="Message type")
    price_millicents: float = Field(default=0, description="Price in millicents USD")
    campaign_id: str = Field(default="", description="Campaign ID if from journey")
    journey_id: str = Field(default="", description="Journey ID if from journey")

    class Config:
        populate_by_name = True


class InboundSMS(BaseModel):
    """Inbound SMS response from subscriber."""

    event_timestamp: datetime = Field(..., description="When the message was received")
    origination_number: str = Field(..., description="Sender phone number")
    destination_number: str = Field(..., description="Your phone number")
    message_body: str = Field(..., description="SMS message content")
    keyword: str = Field(default="", description="Matched keyword if any")
    message_id: str = Field(default="", description="Unique message ID")

    def get_normalized_response(self) -> str:
        """Get normalized (uppercased, trimmed) response text."""
        return self.message_body.strip().upper()

    def is_opt_out(self) -> bool:
        """Check if this is an opt-out response."""
        opt_out_keywords = {"STOP", "UNSUBSCRIBE", "CANCEL", "END", "QUIT"}
        return self.get_normalized_response() in opt_out_keywords

    def is_confirmation(self) -> bool:
        """Check if this is a confirmation response."""
        confirm_keywords = {"YES", "Y", "CONFIRM", "OK", "1"}
        return self.get_normalized_response() in confirm_keywords


class SMSResponse(BaseModel):
    """Stored SMS response in DynamoDB."""

    subscriber_id: str = Field(..., description="Unique subscriber identifier")
    response_timestamp: str = Field(..., description="ISO timestamp of response")
    phone_number: str = Field(..., description="Subscriber phone number")
    response_text: str = Field(..., description="Response message content")
    normalized_response: str = Field(..., description="Normalized response text")
    campaign_id: str = Field(default="", description="Related campaign ID")
    journey_id: str = Field(default="", description="Related journey ID")
    response_date: str = Field(..., description="Date for GSI (YYYY-MM-DD)")
    sentiment: str = Field(default="neutral", description="Response sentiment")
    is_opt_out: bool = Field(default=False, description="Whether this is an opt-out")
    is_confirmation: bool = Field(default=False, description="Whether this confirms")
    ttl: int = Field(..., description="TTL for DynamoDB (epoch seconds)")

    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format."""
        return {
            "subscriber_id": {"S": self.subscriber_id},
            "response_timestamp": {"S": self.response_timestamp},
            "phone_number": {"S": self.phone_number},
            "response_text": {"S": self.response_text},
            "normalized_response": {"S": self.normalized_response},
            "campaign_id": {"S": self.campaign_id},
            "journey_id": {"S": self.journey_id},
            "response_date": {"S": self.response_date},
            "sentiment": {"S": self.sentiment},
            "is_opt_out": {"BOOL": self.is_opt_out},
            "is_confirmation": {"BOOL": self.is_confirmation},
            "ttl": {"N": str(self.ttl)},
        }


class Subscriber(BaseModel):
    """Subscriber information."""

    subscriber_id: str = Field(..., description="Unique subscriber identifier")
    phone_number: str = Field(..., description="Phone number")
    subscription_status: SubscriptionStatus = Field(
        default=SubscriptionStatus.PENDING,
        description="Current subscription status",
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When subscriber was created",
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last update timestamp",
    )
    opt_in_timestamp: datetime | None = Field(
        default=None,
        description="When subscriber opted in",
    )
    opt_out_timestamp: datetime | None = Field(
        default=None,
        description="When subscriber opted out",
    )
    total_messages_sent: int = Field(default=0, description="Total messages sent")
    total_responses: int = Field(default=0, description="Total responses received")
    last_response_at: datetime | None = Field(
        default=None,
        description="Last response timestamp",
    )
    attributes: dict = Field(
        default_factory=dict,
        description="Custom subscriber attributes",
    )

    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format."""
        item = {
            "subscriber_id": {"S": self.subscriber_id},
            "phone_number": {"S": self.phone_number},
            "subscription_status": {"S": self.subscription_status.value},
            "created_at": {"S": self.created_at.isoformat()},
            "updated_at": {"S": self.updated_at.isoformat()},
            "total_messages_sent": {"N": str(self.total_messages_sent)},
            "total_responses": {"N": str(self.total_responses)},
        }

        if self.opt_in_timestamp:
            item["opt_in_timestamp"] = {"S": self.opt_in_timestamp.isoformat()}
        if self.opt_out_timestamp:
            item["opt_out_timestamp"] = {"S": self.opt_out_timestamp.isoformat()}
        if self.last_response_at:
            item["last_response_at"] = {"S": self.last_response_at.isoformat()}
        if self.attributes:
            item["attributes"] = {"S": str(self.attributes)}

        return item


class AnalyticsMetrics(BaseModel):
    """Real-time analytics metrics."""

    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Metrics timestamp",
    )
    period_minutes: int = Field(default=5, description="Aggregation period")
    messages_sent: int = Field(default=0, description="Messages sent in period")
    messages_delivered: int = Field(default=0, description="Messages delivered")
    messages_failed: int = Field(default=0, description="Messages failed")
    responses_received: int = Field(default=0, description="Responses received")
    opt_outs: int = Field(default=0, description="Opt-outs in period")
    confirmations: int = Field(default=0, description="Confirmations in period")
    delivery_rate: float = Field(default=0.0, description="Delivery success rate")
    response_rate: float = Field(default=0.0, description="Response rate")
    total_cost_usd: float = Field(default=0.0, description="Total cost in USD")

    def calculate_rates(self) -> None:
        """Calculate delivery and response rates."""
        if self.messages_sent > 0:
            self.delivery_rate = self.messages_delivered / self.messages_sent
            self.response_rate = self.responses_received / self.messages_sent


class ArchiveRecord(BaseModel):
    """Record for S3 archival."""

    event_type: str
    event_timestamp: str
    subscriber_id: str
    phone_number: str
    message_id: str
    campaign_id: str
    journey_id: str
    record_status: str
    message_type: str
    country_code: str
    price_millicents: float
    response_text: str | None = None
    archived_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat(),
    )

    def to_parquet_dict(self) -> dict:
        """Convert to Parquet-compatible dictionary."""
        return self.model_dump()
