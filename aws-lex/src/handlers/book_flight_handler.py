"""Handler for BookFlight intent."""

from datetime import date, datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from ..common.config import settings
from ..common.exceptions import BookingError, FlightNotFoundError
from ..common.models import CabinClass, LexEvent, Passenger
from ..services.booking_service import BookingService
from ..services.flight_service import FlightService
from ..services.lex_response_service import LexResponseService

logger = Logger()
tracer = Tracer()


@tracer.capture_method
def handle_book_flight(event: LexEvent) -> dict[str, Any]:
    """Handle the BookFlight intent.

    Args:
        event: Lex event

    Returns:
        Lex response
    """
    invocation_source = event.invocation_source
    session_attributes = event.session_state.session_attributes

    if invocation_source == "DialogCodeHook":
        return _validate_slots(event)

    return _fulfill_booking(event, session_attributes)


def _validate_slots(event: LexEvent) -> dict[str, Any]:
    """Validate slot values during dialog.

    Args:
        event: Lex event

    Returns:
        Lex response for slot validation
    """
    slots = _get_slot_values(event)
    session_attributes = event.session_state.session_attributes

    # Validate Origin
    origin = event.get_slot_value("Origin")
    if origin and not _is_valid_airport(origin):
        return LexResponseService.build_elicit_slot_response(
            intent_name="BookFlight",
            slots=slots,
            slot_to_elicit="Origin",
            message=f"'{origin}' is not a valid airport. Please enter a valid city or airport code.",
            session_attributes=session_attributes,
        )

    # Validate Destination
    destination = event.get_slot_value("Destination")
    if destination and not _is_valid_airport(destination):
        return LexResponseService.build_elicit_slot_response(
            intent_name="BookFlight",
            slots=slots,
            slot_to_elicit="Destination",
            message=f"'{destination}' is not a valid airport. Please enter a valid city or airport code.",
            session_attributes=session_attributes,
        )

    # Validate same origin and destination
    if origin and destination and origin.upper() == destination.upper():
        return LexResponseService.build_elicit_slot_response(
            intent_name="BookFlight",
            slots=slots,
            slot_to_elicit="Destination",
            message="Origin and destination cannot be the same. Please choose a different destination.",
            session_attributes=session_attributes,
        )

    # Validate DepartureDate
    departure_date = event.get_slot_value("DepartureDate")
    if departure_date:
        try:
            dep_date = _parse_date(departure_date)
            if dep_date < date.today():
                return LexResponseService.build_elicit_slot_response(
                    intent_name="BookFlight",
                    slots=slots,
                    slot_to_elicit="DepartureDate",
                    message="Departure date cannot be in the past. When would you like to depart?",
                    session_attributes=session_attributes,
                )
            if (dep_date - date.today()).days > settings.booking_advance_days:
                return LexResponseService.build_elicit_slot_response(
                    intent_name="BookFlight",
                    slots=slots,
                    slot_to_elicit="DepartureDate",
                    message=f"Bookings can only be made up to {settings.booking_advance_days} days in advance.",
                    session_attributes=session_attributes,
                )
        except ValueError:
            return LexResponseService.build_elicit_slot_response(
                intent_name="BookFlight",
                slots=slots,
                slot_to_elicit="DepartureDate",
                message="I couldn't understand that date. Please provide a valid date.",
                session_attributes=session_attributes,
            )

    # Validate Passengers
    passengers = event.get_slot_value("Passengers")
    if passengers:
        try:
            num_passengers = int(passengers)
            if num_passengers < 1:
                return LexResponseService.build_elicit_slot_response(
                    intent_name="BookFlight",
                    slots=slots,
                    slot_to_elicit="Passengers",
                    message="You need at least 1 passenger. How many passengers?",
                    session_attributes=session_attributes,
                )
            if num_passengers > settings.max_passengers_per_booking:
                return LexResponseService.build_elicit_slot_response(
                    intent_name="BookFlight",
                    slots=slots,
                    slot_to_elicit="Passengers",
                    message=f"Maximum {settings.max_passengers_per_booking} passengers per booking.",
                    session_attributes=session_attributes,
                )
        except ValueError:
            return LexResponseService.build_elicit_slot_response(
                intent_name="BookFlight",
                slots=slots,
                slot_to_elicit="Passengers",
                message="Please enter a valid number of passengers.",
                session_attributes=session_attributes,
            )

    # All validations passed, delegate back to Lex
    return LexResponseService.build_delegate_response(
        intent_name="BookFlight",
        slots=slots,
        session_attributes=session_attributes,
    )


def _fulfill_booking(event: LexEvent, session_attributes: dict[str, str]) -> dict[str, Any]:
    """Fulfill the booking intent.

    Args:
        event: Lex event
        session_attributes: Session attributes

    Returns:
        Lex response
    """
    origin = event.get_slot_value("Origin")
    destination = event.get_slot_value("Destination")
    departure_date_str = event.get_slot_value("DepartureDate")
    passengers_str = event.get_slot_value("Passengers")
    cabin_class_str = event.get_slot_value("CabinClass")

    departure_date = _parse_date(departure_date_str)
    num_passengers = int(passengers_str)
    cabin_class = CabinClass(cabin_class_str.lower()) if cabin_class_str else CabinClass.ECONOMY

    flight_service = FlightService()
    booking_service = BookingService()

    # Check for selected flight from previous interaction
    selected_flight_id = session_attributes.get("selected_flight_id")

    if selected_flight_id:
        try:
            flight = flight_service.get_flight(selected_flight_id)
        except FlightNotFoundError:
            return LexResponseService.build_fulfillment_response(
                intent_name="BookFlight",
                message="The selected flight is no longer available. Please search again.",
                session_attributes=session_attributes,
                fulfilled=False,
            )
    else:
        # Search for flights
        flights = flight_service.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            passengers=num_passengers,
            cabin_class=cabin_class,
        )

        if not flights:
            return LexResponseService.build_fulfillment_response(
                intent_name="BookFlight",
                message=f"Sorry, no flights found from {origin} to {destination} on {departure_date}.",
                session_attributes=session_attributes,
                fulfilled=False,
            )

        if len(flights) > 1:
            # Multiple flights available - present options
            session_attributes["available_flights"] = ",".join(f.flight_id for f in flights)
            return LexResponseService.build_fulfillment_response(
                intent_name="BookFlight",
                message=LexResponseService.format_flight_list(flights),
                session_attributes=session_attributes,
                fulfilled=False,
            )

        flight = flights[0]

    # Create passengers
    passengers = [
        Passenger(first_name=f"Passenger", last_name=f"{i + 1}")
        for i in range(num_passengers)
    ]

    try:
        booking = booking_service.create_booking(
            flight=flight,
            passengers=passengers,
            cabin_class=cabin_class,
        )

        # Update available seats
        flight_service.update_available_seats(flight.flight_id, -num_passengers)

        return LexResponseService.build_fulfillment_response(
            intent_name="BookFlight",
            message=LexResponseService.format_booking_confirmation(booking),
            session_attributes={},
        )

    except BookingError as e:
        logger.error(f"Booking failed: {e.message}")
        return LexResponseService.build_fulfillment_response(
            intent_name="BookFlight",
            message=f"Sorry, I couldn't complete your booking: {e.message}",
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


def _is_valid_airport(airport: str) -> bool:
    """Check if airport code/city is valid."""
    valid_airports = {
        "LHR", "LONDON", "CDG", "PARIS", "JFK", "NEW YORK", "LAX", "LOS ANGELES",
        "FRA", "FRANKFURT", "AMS", "AMSTERDAM", "BCN", "BARCELONA", "MAD", "MADRID",
        "FCO", "ROME", "MUC", "MUNICH", "ZRH", "ZURICH", "VIE", "VIENNA",
        "DXB", "DUBAI", "SIN", "SINGAPORE", "HKG", "HONG KONG", "NRT", "TOKYO",
    }
    return airport.upper() in valid_airports


def _parse_date(date_str: str) -> date:
    """Parse a date string."""
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Unable to parse date: {date_str}")
