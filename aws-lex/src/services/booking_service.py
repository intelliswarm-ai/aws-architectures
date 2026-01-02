"""Booking service for managing flight reservations."""

import secrets
import string
from datetime import datetime
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Key

from ..common.config import settings
from ..common.exceptions import BookingError, BookingNotFoundError
from ..common.models import Booking, BookingStatus, CabinClass, Flight, Passenger, UpdateType


class BookingService:
    """Service for booking operations."""

    def __init__(self) -> None:
        """Initialize the booking service."""
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.table = self.dynamodb.Table(settings.bookings_table)

    def create_booking(
        self,
        flight: Flight,
        passengers: list[Passenger],
        cabin_class: CabinClass,
        return_date: datetime | None = None,
        customer_email: str | None = None,
        customer_phone: str | None = None,
    ) -> Booking:
        """Create a new booking.

        Args:
            flight: The flight to book
            passengers: List of passengers
            cabin_class: Selected cabin class
            return_date: Optional return date for round trip
            customer_email: Customer email address
            customer_phone: Customer phone number

        Returns:
            Created booking

        Raises:
            BookingError: If booking creation fails
        """
        if len(passengers) > settings.max_passengers_per_booking:
            raise BookingError(
                f"Maximum {settings.max_passengers_per_booking} passengers allowed per booking"
            )

        if flight.available_seats < len(passengers):
            raise BookingError(
                f"Not enough seats available. Requested: {len(passengers)}, "
                f"Available: {flight.available_seats}"
            )

        booking_reference = self._generate_booking_reference()
        total_price = flight.price_per_person * len(passengers)

        booking = Booking(
            booking_reference=booking_reference,
            flight_id=flight.flight_id,
            flight_number=flight.flight_number,
            origin=flight.origin,
            destination=flight.destination,
            departure_date=flight.departure_time.date(),
            return_date=return_date.date() if return_date else None,
            passengers=passengers,
            cabin_class=cabin_class,
            total_price=total_price,
            status=BookingStatus.CONFIRMED,
            customer_email=customer_email,
            customer_phone=customer_phone,
        )

        self.table.put_item(Item=self._booking_to_item(booking))
        return booking

    def get_booking(self, booking_reference: str) -> Booking:
        """Get a booking by reference.

        Args:
            booking_reference: The booking reference code

        Returns:
            Booking details

        Raises:
            BookingNotFoundError: If booking not found
        """
        response = self.table.get_item(Key={"booking_reference": booking_reference.upper()})

        if "Item" not in response:
            raise BookingNotFoundError(booking_reference)

        return self._item_to_booking(response["Item"])

    def update_booking(
        self,
        booking_reference: str,
        update_type: UpdateType,
        new_value: Any,
    ) -> Booking:
        """Update an existing booking.

        Args:
            booking_reference: The booking reference code
            update_type: Type of update to perform
            new_value: New value for the update

        Returns:
            Updated booking

        Raises:
            BookingNotFoundError: If booking not found
            BookingError: If update is not allowed
        """
        booking = self.get_booking(booking_reference)

        if booking.status == BookingStatus.CANCELLED:
            raise BookingError("Cannot update a cancelled booking", booking_reference)

        if booking.status == BookingStatus.COMPLETED:
            raise BookingError("Cannot update a completed booking", booking_reference)

        update_expression = "SET updated_at = :updated_at"
        expression_values: dict[str, Any] = {":updated_at": datetime.utcnow().isoformat()}

        if update_type == UpdateType.DATE:
            update_expression += ", departure_date = :departure_date"
            expression_values[":departure_date"] = new_value
        elif update_type == UpdateType.PASSENGERS:
            update_expression += ", passengers = :passengers"
            expression_values[":passengers"] = new_value
        elif update_type == UpdateType.CABIN_CLASS:
            update_expression += ", cabin_class = :cabin_class"
            expression_values[":cabin_class"] = new_value

        self.table.update_item(
            Key={"booking_reference": booking_reference.upper()},
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values,
        )

        return self.get_booking(booking_reference)

    def cancel_booking(self, booking_reference: str) -> Booking:
        """Cancel an existing booking.

        Args:
            booking_reference: The booking reference code

        Returns:
            Cancelled booking

        Raises:
            BookingNotFoundError: If booking not found
            BookingError: If cancellation is not allowed
        """
        booking = self.get_booking(booking_reference)

        if booking.status == BookingStatus.CANCELLED:
            raise BookingError("Booking is already cancelled", booking_reference)

        if booking.status == BookingStatus.COMPLETED:
            raise BookingError("Cannot cancel a completed booking", booking_reference)

        self.table.update_item(
            Key={"booking_reference": booking_reference.upper()},
            UpdateExpression="SET #status = :status, updated_at = :updated_at",
            ExpressionAttributeNames={"#status": "status"},
            ExpressionAttributeValues={
                ":status": BookingStatus.CANCELLED.value,
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )

        booking.status = BookingStatus.CANCELLED
        return booking

    def get_bookings_by_customer(self, customer_email: str) -> list[Booking]:
        """Get all bookings for a customer.

        Args:
            customer_email: Customer email address

        Returns:
            List of bookings
        """
        response = self.table.query(
            IndexName="customer-email-index",
            KeyConditionExpression=Key("customer_email").eq(customer_email),
        )

        return [self._item_to_booking(item) for item in response.get("Items", [])]

    def _generate_booking_reference(self) -> str:
        """Generate a unique booking reference code."""
        chars = string.ascii_uppercase + string.digits
        while True:
            reference = "".join(secrets.choice(chars) for _ in range(6))
            try:
                self.get_booking(reference)
            except BookingNotFoundError:
                return reference

    def _booking_to_item(self, booking: Booking) -> dict[str, Any]:
        """Convert Booking model to DynamoDB item."""
        passengers_data = [
            {
                "first_name": p.first_name,
                "last_name": p.last_name,
                "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
                "passport_number": p.passport_number,
                "seat_number": p.seat_number,
                "seat_preference": p.seat_preference.value if p.seat_preference else None,
                "checked_in": p.checked_in,
            }
            for p in booking.passengers
        ]

        return {
            "booking_reference": booking.booking_reference,
            "flight_id": booking.flight_id,
            "flight_number": booking.flight_number,
            "origin": booking.origin,
            "destination": booking.destination,
            "departure_date": booking.departure_date.isoformat(),
            "return_date": booking.return_date.isoformat() if booking.return_date else None,
            "passengers": passengers_data,
            "cabin_class": booking.cabin_class.value,
            "total_price": str(booking.total_price),
            "status": booking.status.value,
            "created_at": booking.created_at.isoformat(),
            "updated_at": booking.updated_at.isoformat(),
            "customer_email": booking.customer_email,
            "customer_phone": booking.customer_phone,
        }

    def _item_to_booking(self, item: dict[str, Any]) -> Booking:
        """Convert DynamoDB item to Booking model."""
        from datetime import date as date_type

        passengers = [
            Passenger(
                first_name=p["first_name"],
                last_name=p["last_name"],
                date_of_birth=(
                    date_type.fromisoformat(p["date_of_birth"]) if p.get("date_of_birth") else None
                ),
                passport_number=p.get("passport_number"),
                seat_number=p.get("seat_number"),
                seat_preference=p.get("seat_preference"),
                checked_in=p.get("checked_in", False),
            )
            for p in item.get("passengers", [])
        ]

        return Booking(
            booking_reference=item["booking_reference"],
            flight_id=item["flight_id"],
            flight_number=item["flight_number"],
            origin=item["origin"],
            destination=item["destination"],
            departure_date=date_type.fromisoformat(item["departure_date"]),
            return_date=(
                date_type.fromisoformat(item["return_date"]) if item.get("return_date") else None
            ),
            passengers=passengers,
            cabin_class=CabinClass(item["cabin_class"]),
            total_price=Decimal(item["total_price"]),
            status=BookingStatus(item["status"]),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            customer_email=item.get("customer_email"),
            customer_phone=item.get("customer_phone"),
        )
