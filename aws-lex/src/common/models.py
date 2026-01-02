"""Pydantic data models for AWS Lex airline chatbot."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CabinClass(str, Enum):
    """Cabin class options."""

    ECONOMY = "economy"
    BUSINESS = "business"
    FIRST = "first"


class BookingStatus(str, Enum):
    """Booking status states."""

    CONFIRMED = "confirmed"
    PENDING = "pending"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class CheckInStatus(str, Enum):
    """Check-in status states."""

    PENDING = "pending"
    CHECKED_IN = "checked_in"
    BOARDED = "boarded"


class SeatPreference(str, Enum):
    """Seat preference options."""

    WINDOW = "window"
    MIDDLE = "middle"
    AISLE = "aisle"


class UpdateType(str, Enum):
    """Booking update types."""

    DATE = "date"
    PASSENGERS = "passengers"
    SEATS = "seats"
    CABIN_CLASS = "cabin_class"


class IntentState(str, Enum):
    """Lex intent states."""

    IN_PROGRESS = "InProgress"
    FULFILLED = "Fulfilled"
    FAILED = "Failed"
    READY_FOR_FULFILLMENT = "ReadyForFulfillment"


class DialogActionType(str, Enum):
    """Lex dialog action types."""

    CLOSE = "Close"
    CONFIRM_INTENT = "ConfirmIntent"
    DELEGATE = "Delegate"
    ELICIT_INTENT = "ElicitIntent"
    ELICIT_SLOT = "ElicitSlot"


class Passenger(BaseModel):
    """Passenger information."""

    first_name: str
    last_name: str
    date_of_birth: date | None = None
    passport_number: str | None = None
    seat_number: str | None = None
    seat_preference: SeatPreference | None = None
    checked_in: bool = False


class Flight(BaseModel):
    """Flight information."""

    flight_id: str
    flight_number: str
    airline: str
    origin: str
    destination: str
    departure_time: datetime
    arrival_time: datetime
    duration_minutes: int
    price_per_person: Decimal
    available_seats: int
    cabin_class: CabinClass = CabinClass.ECONOMY


class Booking(BaseModel):
    """Booking record."""

    booking_reference: str
    flight_id: str
    flight_number: str
    origin: str
    destination: str
    departure_date: date
    return_date: date | None = None
    passengers: list[Passenger]
    cabin_class: CabinClass
    total_price: Decimal
    status: BookingStatus = BookingStatus.CONFIRMED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    customer_email: str | None = None
    customer_phone: str | None = None


class CheckIn(BaseModel):
    """Check-in record."""

    checkin_id: str
    booking_reference: str
    passenger_name: str
    flight_number: str
    seat_number: str
    boarding_pass_url: str | None = None
    status: CheckInStatus = CheckInStatus.CHECKED_IN
    checked_in_at: datetime = Field(default_factory=datetime.utcnow)


class SlotValue(BaseModel):
    """Lex slot value."""

    value: dict[str, Any] | None = None
    shape: str | None = None
    values: list[dict[str, Any]] | None = None


class DialogAction(BaseModel):
    """Lex dialog action."""

    type: DialogActionType
    slot_to_elicit: str | None = None
    slot_elicitation_style: str | None = None


class Intent(BaseModel):
    """Lex intent."""

    name: str
    slots: dict[str, SlotValue | None] = {}
    state: IntentState = IntentState.IN_PROGRESS
    confirmation_state: str | None = None


class SessionState(BaseModel):
    """Lex session state."""

    dialog_action: DialogAction | None = None
    intent: Intent | None = None
    session_attributes: dict[str, str] = {}
    active_contexts: list[dict[str, Any]] = []
    runtime_hints: dict[str, Any] = {}


class Message(BaseModel):
    """Lex response message."""

    content_type: str = "PlainText"
    content: str
    image_response_card: dict[str, Any] | None = None


class LexEvent(BaseModel):
    """Lex V2 input event."""

    session_id: str
    input_transcript: str | None = None
    interpretations: list[dict[str, Any]] = []
    proposed_next_state: dict[str, Any] | None = None
    request_attributes: dict[str, str] = {}
    session_state: SessionState
    input_mode: str = "Text"
    invocation_source: str = "FulfillmentCodeHook"
    bot: dict[str, Any] = {}

    def get_intent_name(self) -> str:
        """Get the current intent name."""
        if self.session_state.intent:
            return self.session_state.intent.name
        return ""

    def get_slot_value(self, slot_name: str) -> str | None:
        """Get a slot value by name."""
        if not self.session_state.intent:
            return None
        slot = self.session_state.intent.slots.get(slot_name)
        if slot and slot.value:
            return slot.value.get("interpretedValue") or slot.value.get("originalValue")
        return None

    def get_session_attribute(self, key: str) -> str | None:
        """Get a session attribute by key."""
        return self.session_state.session_attributes.get(key)


class LexResponse(BaseModel):
    """Lex V2 response."""

    session_state: SessionState
    messages: list[Message] = []
    request_attributes: dict[str, str] = {}

    @classmethod
    def close(
        cls,
        intent_name: str,
        state: IntentState,
        message: str,
        session_attributes: dict[str, str] | None = None,
    ) -> "LexResponse":
        """Create a close dialog response."""
        return cls(
            session_state=SessionState(
                dialog_action=DialogAction(type=DialogActionType.CLOSE),
                intent=Intent(name=intent_name, state=state),
                session_attributes=session_attributes or {},
            ),
            messages=[Message(content=message)],
        )

    @classmethod
    def elicit_slot(
        cls,
        intent_name: str,
        slots: dict[str, SlotValue | None],
        slot_to_elicit: str,
        message: str,
        session_attributes: dict[str, str] | None = None,
    ) -> "LexResponse":
        """Create an elicit slot response."""
        return cls(
            session_state=SessionState(
                dialog_action=DialogAction(
                    type=DialogActionType.ELICIT_SLOT,
                    slot_to_elicit=slot_to_elicit,
                ),
                intent=Intent(name=intent_name, slots=slots, state=IntentState.IN_PROGRESS),
                session_attributes=session_attributes or {},
            ),
            messages=[Message(content=message)],
        )

    @classmethod
    def delegate(
        cls,
        intent_name: str,
        slots: dict[str, SlotValue | None],
        session_attributes: dict[str, str] | None = None,
    ) -> "LexResponse":
        """Create a delegate response to let Lex handle dialog."""
        return cls(
            session_state=SessionState(
                dialog_action=DialogAction(type=DialogActionType.DELEGATE),
                intent=Intent(name=intent_name, slots=slots, state=IntentState.IN_PROGRESS),
                session_attributes=session_attributes or {},
            ),
        )

    @classmethod
    def confirm_intent(
        cls,
        intent_name: str,
        slots: dict[str, SlotValue | None],
        message: str,
        session_attributes: dict[str, str] | None = None,
    ) -> "LexResponse":
        """Create a confirm intent response."""
        return cls(
            session_state=SessionState(
                dialog_action=DialogAction(type=DialogActionType.CONFIRM_INTENT),
                intent=Intent(name=intent_name, slots=slots, state=IntentState.IN_PROGRESS),
                session_attributes=session_attributes or {},
            ),
            messages=[Message(content=message)],
        )
