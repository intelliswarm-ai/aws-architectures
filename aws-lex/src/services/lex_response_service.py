"""Lex response service for formatting bot responses."""

from typing import Any

from ..common.models import (
    Booking,
    CheckIn,
    DialogAction,
    DialogActionType,
    Flight,
    Intent,
    IntentState,
    LexResponse,
    Message,
    SessionState,
    SlotValue,
)


class LexResponseService:
    """Service for building Lex V2 responses."""

    @staticmethod
    def build_fulfillment_response(
        intent_name: str,
        message: str,
        session_attributes: dict[str, str] | None = None,
        fulfilled: bool = True,
    ) -> dict[str, Any]:
        """Build a fulfillment response.

        Args:
            intent_name: Name of the intent
            message: Response message
            session_attributes: Optional session attributes
            fulfilled: Whether the intent was fulfilled

        Returns:
            Lex response dictionary
        """
        state = IntentState.FULFILLED if fulfilled else IntentState.FAILED
        response = LexResponse.close(
            intent_name=intent_name,
            state=state,
            message=message,
            session_attributes=session_attributes,
        )
        return response.model_dump(by_alias=True, exclude_none=True)

    @staticmethod
    def build_elicit_slot_response(
        intent_name: str,
        slots: dict[str, Any],
        slot_to_elicit: str,
        message: str,
        session_attributes: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build an elicit slot response.

        Args:
            intent_name: Name of the intent
            slots: Current slot values
            slot_to_elicit: Slot to elicit from user
            message: Prompt message
            session_attributes: Optional session attributes

        Returns:
            Lex response dictionary
        """
        slot_values = {
            k: SlotValue(value=v) if v else None for k, v in slots.items()
        }
        response = LexResponse.elicit_slot(
            intent_name=intent_name,
            slots=slot_values,
            slot_to_elicit=slot_to_elicit,
            message=message,
            session_attributes=session_attributes,
        )
        return response.model_dump(by_alias=True, exclude_none=True)

    @staticmethod
    def build_delegate_response(
        intent_name: str,
        slots: dict[str, Any],
        session_attributes: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build a delegate response.

        Args:
            intent_name: Name of the intent
            slots: Current slot values
            session_attributes: Optional session attributes

        Returns:
            Lex response dictionary
        """
        slot_values = {
            k: SlotValue(value=v) if v else None for k, v in slots.items()
        }
        response = LexResponse.delegate(
            intent_name=intent_name,
            slots=slot_values,
            session_attributes=session_attributes,
        )
        return response.model_dump(by_alias=True, exclude_none=True)

    @staticmethod
    def build_confirm_response(
        intent_name: str,
        slots: dict[str, Any],
        message: str,
        session_attributes: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """Build a confirm intent response.

        Args:
            intent_name: Name of the intent
            slots: Current slot values
            message: Confirmation message
            session_attributes: Optional session attributes

        Returns:
            Lex response dictionary
        """
        slot_values = {
            k: SlotValue(value=v) if v else None for k, v in slots.items()
        }
        response = LexResponse.confirm_intent(
            intent_name=intent_name,
            slots=slot_values,
            message=message,
            session_attributes=session_attributes,
        )
        return response.model_dump(by_alias=True, exclude_none=True)

    @staticmethod
    def format_flight_list(flights: list[Flight]) -> str:
        """Format a list of flights for display.

        Args:
            flights: List of flights

        Returns:
            Formatted flight list message
        """
        if not flights:
            return "No flights found matching your criteria."

        lines = [f"I found {len(flights)} flight(s):"]
        for i, flight in enumerate(flights, 1):
            time_str = flight.departure_time.strftime("%H:%M")
            lines.append(
                f"{i}. {flight.flight_number} - {time_str} - "
                f"${flight.price_per_person}/person ({flight.available_seats} seats left)"
            )

        lines.append("\nWhich flight would you like to book?")
        return "\n".join(lines)

    @staticmethod
    def format_booking_confirmation(booking: Booking) -> str:
        """Format a booking confirmation message.

        Args:
            booking: The booking

        Returns:
            Formatted booking confirmation
        """
        passenger_names = ", ".join(
            f"{p.first_name} {p.last_name}" for p in booking.passengers
        )

        return (
            f"Your flight has been booked!\n\n"
            f"Booking Reference: {booking.booking_reference}\n"
            f"Flight: {booking.flight_number}\n"
            f"Route: {booking.origin} → {booking.destination}\n"
            f"Date: {booking.departure_date.strftime('%B %d, %Y')}\n"
            f"Passengers: {passenger_names}\n"
            f"Class: {booking.cabin_class.value.title()}\n"
            f"Total: ${booking.total_price}\n\n"
            f"Is there anything else I can help you with?"
        )

    @staticmethod
    def format_booking_details(booking: Booking) -> str:
        """Format booking details for display.

        Args:
            booking: The booking

        Returns:
            Formatted booking details
        """
        passenger_names = ", ".join(
            f"{p.first_name} {p.last_name}" for p in booking.passengers
        )

        return (
            f"Booking Reference: {booking.booking_reference}\n"
            f"Status: {booking.status.value.title()}\n"
            f"Flight: {booking.flight_number}\n"
            f"Route: {booking.origin} → {booking.destination}\n"
            f"Date: {booking.departure_date.strftime('%B %d, %Y')}\n"
            f"Passengers: {passenger_names}\n"
            f"Class: {booking.cabin_class.value.title()}\n"
            f"Total: ${booking.total_price}"
        )

    @staticmethod
    def format_checkin_confirmation(checkin: CheckIn) -> str:
        """Format check-in confirmation message.

        Args:
            checkin: The check-in

        Returns:
            Formatted check-in confirmation
        """
        return (
            f"Check-in complete!\n\n"
            f"Passenger: {checkin.passenger_name}\n"
            f"Flight: {checkin.flight_number}\n"
            f"Seat: {checkin.seat_number}\n\n"
            f"Your boarding pass is available at:\n{checkin.boarding_pass_url}\n\n"
            f"Is there anything else I can help you with?"
        )

    @staticmethod
    def format_update_confirmation(booking: Booking, update_type: str) -> str:
        """Format booking update confirmation.

        Args:
            booking: The updated booking
            update_type: Type of update made

        Returns:
            Formatted update confirmation
        """
        return (
            f"Your booking has been updated!\n\n"
            f"Update type: {update_type}\n"
            f"Booking Reference: {booking.booking_reference}\n"
            f"Flight: {booking.flight_number}\n"
            f"Date: {booking.departure_date.strftime('%B %d, %Y')}\n\n"
            f"Is there anything else I can help you with?"
        )
