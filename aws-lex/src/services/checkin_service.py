"""Check-in service for managing passenger check-ins."""

import secrets
import string
from datetime import datetime, timedelta
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from ..common.config import settings
from ..common.exceptions import CheckInError, CheckInWindowError
from ..common.models import Booking, BookingStatus, CheckIn, CheckInStatus, SeatPreference


class CheckInService:
    """Service for check-in operations."""

    def __init__(self) -> None:
        """Initialize the check-in service."""
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.table = self.dynamodb.Table(settings.checkins_table)

    def check_in_passenger(
        self,
        booking: Booking,
        passenger_name: str,
        seat_preference: SeatPreference | None = None,
    ) -> CheckIn:
        """Check in a passenger for their flight.

        Args:
            booking: The booking to check in
            passenger_name: Passenger's first name
            seat_preference: Optional seat preference

        Returns:
            Check-in confirmation

        Raises:
            CheckInError: If check-in fails
            CheckInWindowError: If outside check-in window
        """
        if booking.status == BookingStatus.CANCELLED:
            raise CheckInError(
                "Cannot check in for a cancelled booking",
                booking_reference=booking.booking_reference,
            )

        departure_datetime = datetime.combine(booking.departure_date, datetime.min.time())
        hours_until_departure = (departure_datetime - datetime.now()).total_seconds() / 3600

        if hours_until_departure > settings.checkin_window_hours:
            raise CheckInWindowError(
                booking_reference=booking.booking_reference,
                hours_until_departure=int(hours_until_departure),
            )

        if hours_until_departure < 0:
            raise CheckInError(
                "Flight has already departed",
                booking_reference=booking.booking_reference,
                reason="DEPARTED",
            )

        passenger = None
        for p in booking.passengers:
            if p.first_name.lower() == passenger_name.lower():
                passenger = p
                break

        if not passenger:
            raise CheckInError(
                f"Passenger '{passenger_name}' not found on booking",
                booking_reference=booking.booking_reference,
                reason="PASSENGER_NOT_FOUND",
            )

        if passenger.checked_in:
            raise CheckInError(
                f"Passenger '{passenger_name}' is already checked in",
                booking_reference=booking.booking_reference,
                reason="ALREADY_CHECKED_IN",
            )

        seat_number = self._assign_seat(
            booking.flight_number,
            seat_preference or passenger.seat_preference,
        )

        checkin_id = self._generate_checkin_id()
        boarding_pass_url = self._generate_boarding_pass_url(checkin_id)

        checkin = CheckIn(
            checkin_id=checkin_id,
            booking_reference=booking.booking_reference,
            passenger_name=f"{passenger.first_name} {passenger.last_name}",
            flight_number=booking.flight_number,
            seat_number=seat_number,
            boarding_pass_url=boarding_pass_url,
            status=CheckInStatus.CHECKED_IN,
        )

        self.table.put_item(Item=self._checkin_to_item(checkin))
        return checkin

    def get_checkin(self, checkin_id: str) -> CheckIn | None:
        """Get check-in by ID.

        Args:
            checkin_id: The check-in ID

        Returns:
            Check-in details or None if not found
        """
        response = self.table.get_item(Key={"checkin_id": checkin_id})
        if "Item" not in response:
            return None
        return self._item_to_checkin(response["Item"])

    def get_checkins_by_booking(self, booking_reference: str) -> list[CheckIn]:
        """Get all check-ins for a booking.

        Args:
            booking_reference: The booking reference

        Returns:
            List of check-ins
        """
        response = self.table.query(
            IndexName="booking-reference-index",
            KeyConditionExpression=Key("booking_reference").eq(booking_reference.upper()),
        )

        return [self._item_to_checkin(item) for item in response.get("Items", [])]

    def is_passenger_checked_in(self, booking_reference: str, passenger_name: str) -> bool:
        """Check if a passenger is already checked in.

        Args:
            booking_reference: The booking reference
            passenger_name: Passenger's name

        Returns:
            True if checked in, False otherwise
        """
        checkins = self.get_checkins_by_booking(booking_reference)
        return any(
            checkin.passenger_name.lower().startswith(passenger_name.lower())
            for checkin in checkins
        )

    def _assign_seat(
        self,
        flight_number: str,
        preference: SeatPreference | None,
    ) -> str:
        """Assign a seat based on preference and availability.

        Args:
            flight_number: The flight number
            preference: Optional seat preference

        Returns:
            Assigned seat number
        """
        row = secrets.randbelow(30) + 1

        if preference == SeatPreference.WINDOW:
            column = secrets.choice(["A", "F"])
        elif preference == SeatPreference.AISLE:
            column = secrets.choice(["C", "D"])
        else:
            column = secrets.choice(["A", "B", "C", "D", "E", "F"])

        return f"{row}{column}"

    def _generate_checkin_id(self) -> str:
        """Generate a unique check-in ID."""
        chars = string.ascii_uppercase + string.digits
        return "CI" + "".join(secrets.choice(chars) for _ in range(8))

    def _generate_boarding_pass_url(self, checkin_id: str) -> str:
        """Generate a boarding pass URL.

        Args:
            checkin_id: The check-in ID

        Returns:
            URL to boarding pass
        """
        return f"https://airline.example.com/boarding-pass/{checkin_id}"

    def _checkin_to_item(self, checkin: CheckIn) -> dict[str, Any]:
        """Convert CheckIn model to DynamoDB item."""
        return {
            "checkin_id": checkin.checkin_id,
            "booking_reference": checkin.booking_reference,
            "passenger_name": checkin.passenger_name,
            "flight_number": checkin.flight_number,
            "seat_number": checkin.seat_number,
            "boarding_pass_url": checkin.boarding_pass_url,
            "status": checkin.status.value,
            "checked_in_at": checkin.checked_in_at.isoformat(),
        }

    def _item_to_checkin(self, item: dict[str, Any]) -> CheckIn:
        """Convert DynamoDB item to CheckIn model."""
        return CheckIn(
            checkin_id=item["checkin_id"],
            booking_reference=item["booking_reference"],
            passenger_name=item["passenger_name"],
            flight_number=item["flight_number"],
            seat_number=item["seat_number"],
            boarding_pass_url=item.get("boarding_pass_url"),
            status=CheckInStatus(item["status"]),
            checked_in_at=datetime.fromisoformat(item["checked_in_at"]),
        )
