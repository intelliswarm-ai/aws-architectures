"""Handler for UpdateBooking intent."""

from datetime import date, datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from ..common.exceptions import BookingError, BookingNotFoundError
from ..common.models import LexEvent, UpdateType
from ..services.booking_service import BookingService
from ..services.lex_response_service import LexResponseService

logger = Logger()
tracer = Tracer()


@tracer.capture_method
def handle_update_booking(event: LexEvent) -> dict[str, Any]:
    """Handle the UpdateBooking intent.

    Args:
        event: Lex event

    Returns:
        Lex response
    """
    invocation_source = event.invocation_source
    session_attributes = event.session_state.session_attributes

    if invocation_source == "DialogCodeHook":
        return _validate_slots(event)

    return _fulfill_update(event, session_attributes)


def _validate_slots(event: LexEvent) -> dict[str, Any]:
    """Validate slot values during dialog.

    Args:
        event: Lex event

    Returns:
        Lex response for slot validation
    """
    slots = _get_slot_values(event)
    session_attributes = event.session_state.session_attributes
    booking_service = BookingService()

    # Validate BookingReference
    booking_ref = event.get_slot_value("BookingReference")
    if booking_ref:
        try:
            booking = booking_service.get_booking(booking_ref)
            # Store booking info in session for later use
            session_attributes["booking_reference"] = booking.booking_reference
            session_attributes["booking_status"] = booking.status.value
        except BookingNotFoundError:
            return LexResponseService.build_elicit_slot_response(
                intent_name="UpdateBooking",
                slots=slots,
                slot_to_elicit="BookingReference",
                message=f"I couldn't find a booking with reference '{booking_ref}'. Please check and try again.",
                session_attributes=session_attributes,
            )

    # Validate UpdateType
    update_type = event.get_slot_value("UpdateType")
    if update_type:
        valid_types = ["date", "passengers", "seats", "cabin"]
        if update_type.lower() not in valid_types:
            return LexResponseService.build_elicit_slot_response(
                intent_name="UpdateBooking",
                slots=slots,
                slot_to_elicit="UpdateType",
                message="What would you like to update? You can change the date, passengers, seats, or cabin class.",
                session_attributes=session_attributes,
            )

    # Validate NewValue based on UpdateType
    new_value = event.get_slot_value("NewValue")
    if new_value and update_type:
        validation_result = _validate_new_value(update_type, new_value)
        if validation_result:
            return LexResponseService.build_elicit_slot_response(
                intent_name="UpdateBooking",
                slots=slots,
                slot_to_elicit="NewValue",
                message=validation_result,
                session_attributes=session_attributes,
            )

    # All validations passed
    return LexResponseService.build_delegate_response(
        intent_name="UpdateBooking",
        slots=slots,
        session_attributes=session_attributes,
    )


def _fulfill_update(event: LexEvent, session_attributes: dict[str, str]) -> dict[str, Any]:
    """Fulfill the update booking intent.

    Args:
        event: Lex event
        session_attributes: Session attributes

    Returns:
        Lex response
    """
    booking_ref = event.get_slot_value("BookingReference")
    update_type_str = event.get_slot_value("UpdateType")
    new_value = event.get_slot_value("NewValue")

    booking_service = BookingService()

    try:
        # Map string to UpdateType enum
        update_type_map = {
            "date": UpdateType.DATE,
            "passengers": UpdateType.PASSENGERS,
            "seats": UpdateType.SEATS,
            "cabin": UpdateType.CABIN_CLASS,
        }
        update_type = update_type_map.get(update_type_str.lower(), UpdateType.DATE)

        # Process the new value based on update type
        processed_value = _process_new_value(update_type, new_value)

        booking = booking_service.update_booking(
            booking_reference=booking_ref,
            update_type=update_type,
            new_value=processed_value,
        )

        return LexResponseService.build_fulfillment_response(
            intent_name="UpdateBooking",
            message=LexResponseService.format_update_confirmation(booking, update_type_str),
            session_attributes={},
        )

    except BookingNotFoundError:
        return LexResponseService.build_fulfillment_response(
            intent_name="UpdateBooking",
            message=f"I couldn't find booking {booking_ref}. Please check your booking reference.",
            session_attributes=session_attributes,
            fulfilled=False,
        )

    except BookingError as e:
        logger.error(f"Update failed: {e.message}")
        return LexResponseService.build_fulfillment_response(
            intent_name="UpdateBooking",
            message=f"Sorry, I couldn't update your booking: {e.message}",
            session_attributes=session_attributes,
            fulfilled=False,
        )


def _get_slot_values(event: LexEvent) -> dict[str, Any]:
    """Extract slot values from event."""
    if not event.session_state.intent:
        return {}
    return {
        name: slot.value if slot else None
        for name, slot in event.session_state.intent.slots.items()
    }


def _validate_new_value(update_type: str, value: str) -> str | None:
    """Validate the new value based on update type.

    Returns error message if invalid, None if valid.
    """
    update_type = update_type.lower()

    if update_type == "date":
        try:
            parsed_date = _parse_date(value)
            if parsed_date < date.today():
                return "The new date cannot be in the past. Please provide a future date."
        except ValueError:
            return "I couldn't understand that date. Please provide a valid date."

    elif update_type == "passengers":
        try:
            num = int(value)
            if num < 1 or num > 9:
                return "Number of passengers must be between 1 and 9."
        except ValueError:
            return "Please provide a valid number of passengers."

    elif update_type == "cabin":
        valid_cabins = ["economy", "business", "first"]
        if value.lower() not in valid_cabins:
            return "Please choose economy, business, or first class."

    return None


def _process_new_value(update_type: UpdateType, value: str) -> Any:
    """Process the new value for storage."""
    if update_type == UpdateType.DATE:
        return _parse_date(value).isoformat()
    elif update_type == UpdateType.PASSENGERS:
        return int(value)
    elif update_type == UpdateType.CABIN_CLASS:
        return value.lower()
    return value


def _parse_date(date_str: str) -> date:
    """Parse a date string."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")
