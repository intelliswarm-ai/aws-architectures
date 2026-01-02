"""Handler for CheckIn intent."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer

from ..common.exceptions import BookingNotFoundError, CheckInError, CheckInWindowError
from ..common.models import LexEvent, SeatPreference
from ..services.booking_service import BookingService
from ..services.checkin_service import CheckInService
from ..services.lex_response_service import LexResponseService

logger = Logger()
tracer = Tracer()


@tracer.capture_method
def handle_check_in(event: LexEvent) -> dict[str, Any]:
    """Handle the CheckIn intent.

    Args:
        event: Lex event

    Returns:
        Lex response
    """
    invocation_source = event.invocation_source
    session_attributes = event.session_state.session_attributes

    if invocation_source == "DialogCodeHook":
        return _validate_slots(event)

    return _fulfill_checkin(event, session_attributes)


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
    checkin_service = CheckInService()

    # Validate BookingReference
    booking_ref = event.get_slot_value("BookingReference")
    if booking_ref:
        try:
            booking = booking_service.get_booking(booking_ref)
            session_attributes["booking_reference"] = booking.booking_reference
            session_attributes["flight_number"] = booking.flight_number

            # List passengers for context
            passenger_names = [p.first_name for p in booking.passengers]
            session_attributes["passengers"] = ",".join(passenger_names)

        except BookingNotFoundError:
            return LexResponseService.build_elicit_slot_response(
                intent_name="CheckIn",
                slots=slots,
                slot_to_elicit="BookingReference",
                message=f"I couldn't find booking '{booking_ref}'. Please check and try again.",
                session_attributes=session_attributes,
            )

    # Validate PassengerName
    passenger_name = event.get_slot_value("PassengerName")
    if passenger_name and booking_ref:
        try:
            booking = booking_service.get_booking(booking_ref)

            # Check if passenger exists on booking
            passenger_found = any(
                p.first_name.lower() == passenger_name.lower()
                for p in booking.passengers
            )

            if not passenger_found:
                passenger_list = ", ".join(p.first_name for p in booking.passengers)
                return LexResponseService.build_elicit_slot_response(
                    intent_name="CheckIn",
                    slots=slots,
                    slot_to_elicit="PassengerName",
                    message=(
                        f"'{passenger_name}' is not on this booking. "
                        f"The passengers are: {passenger_list}. "
                        "Which passenger would you like to check in?"
                    ),
                    session_attributes=session_attributes,
                )

            # Check if already checked in
            if checkin_service.is_passenger_checked_in(booking_ref, passenger_name):
                return LexResponseService.build_fulfillment_response(
                    intent_name="CheckIn",
                    message=f"{passenger_name} is already checked in for this flight.",
                    session_attributes=session_attributes,
                    fulfilled=True,
                )

        except BookingNotFoundError:
            pass  # Already validated above

    # Validate SeatPreference
    seat_pref = event.get_slot_value("SeatPreference")
    if seat_pref:
        valid_prefs = ["window", "middle", "aisle"]
        if seat_pref.lower() not in valid_prefs:
            return LexResponseService.build_elicit_slot_response(
                intent_name="CheckIn",
                slots=slots,
                slot_to_elicit="SeatPreference",
                message="Would you prefer a window, middle, or aisle seat?",
                session_attributes=session_attributes,
            )

    # All validations passed
    return LexResponseService.build_delegate_response(
        intent_name="CheckIn",
        slots=slots,
        session_attributes=session_attributes,
    )


def _fulfill_checkin(event: LexEvent, session_attributes: dict[str, str]) -> dict[str, Any]:
    """Fulfill the check-in intent.

    Args:
        event: Lex event
        session_attributes: Session attributes

    Returns:
        Lex response
    """
    booking_ref = event.get_slot_value("BookingReference")
    passenger_name = event.get_slot_value("PassengerName")
    seat_pref_str = event.get_slot_value("SeatPreference")

    booking_service = BookingService()
    checkin_service = CheckInService()

    try:
        booking = booking_service.get_booking(booking_ref)

        # Parse seat preference
        seat_preference = None
        if seat_pref_str:
            seat_pref_map = {
                "window": SeatPreference.WINDOW,
                "middle": SeatPreference.MIDDLE,
                "aisle": SeatPreference.AISLE,
            }
            seat_preference = seat_pref_map.get(seat_pref_str.lower())

        checkin = checkin_service.check_in_passenger(
            booking=booking,
            passenger_name=passenger_name,
            seat_preference=seat_preference,
        )

        return LexResponseService.build_fulfillment_response(
            intent_name="CheckIn",
            message=LexResponseService.format_checkin_confirmation(checkin),
            session_attributes={},
        )

    except BookingNotFoundError:
        return LexResponseService.build_fulfillment_response(
            intent_name="CheckIn",
            message=f"I couldn't find booking {booking_ref}. Please check your booking reference.",
            session_attributes=session_attributes,
            fulfilled=False,
        )

    except CheckInWindowError as e:
        return LexResponseService.build_fulfillment_response(
            intent_name="CheckIn",
            message=e.message,
            session_attributes=session_attributes,
            fulfilled=False,
        )

    except CheckInError as e:
        logger.error(f"Check-in failed: {e.message}")
        return LexResponseService.build_fulfillment_response(
            intent_name="CheckIn",
            message=f"Sorry, I couldn't complete check-in: {e.message}",
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
