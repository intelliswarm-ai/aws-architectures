"""Flight service for searching and managing flights."""

from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr, Key

from ..common.config import settings
from ..common.exceptions import FlightNotFoundError
from ..common.models import CabinClass, Flight


class FlightService:
    """Service for flight operations."""

    def __init__(self) -> None:
        """Initialize the flight service."""
        self.dynamodb = boto3.resource("dynamodb", region_name=settings.aws_region)
        self.table = self.dynamodb.Table(settings.flights_table)

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: date,
        passengers: int = 1,
        cabin_class: CabinClass | None = None,
    ) -> list[Flight]:
        """Search for available flights.

        Args:
            origin: Departure city/airport code
            destination: Arrival city/airport code
            departure_date: Date of departure
            passengers: Number of passengers
            cabin_class: Optional cabin class filter

        Returns:
            List of available flights matching criteria
        """
        filter_expression = (
            Attr("origin").eq(origin.upper())
            & Attr("destination").eq(destination.upper())
            & Attr("available_seats").gte(passengers)
        )

        if cabin_class:
            filter_expression = filter_expression & Attr("cabin_class").eq(cabin_class.value)

        departure_start = datetime.combine(departure_date, datetime.min.time())
        departure_end = datetime.combine(departure_date, datetime.max.time())

        response = self.table.scan(
            FilterExpression=filter_expression
            & Attr("departure_time").between(
                departure_start.isoformat(), departure_end.isoformat()
            )
        )

        flights = []
        for item in response.get("Items", []):
            flights.append(self._item_to_flight(item))

        flights.sort(key=lambda f: f.departure_time)
        return flights

    def get_flight(self, flight_id: str) -> Flight:
        """Get a flight by ID.

        Args:
            flight_id: The flight ID

        Returns:
            Flight details

        Raises:
            FlightNotFoundError: If flight not found
        """
        response = self.table.get_item(Key={"flight_id": flight_id})

        if "Item" not in response:
            raise FlightNotFoundError(flight_id=flight_id)

        return self._item_to_flight(response["Item"])

    def update_available_seats(self, flight_id: str, seats_change: int) -> None:
        """Update available seats for a flight.

        Args:
            flight_id: The flight ID
            seats_change: Number of seats to add (positive) or remove (negative)
        """
        self.table.update_item(
            Key={"flight_id": flight_id},
            UpdateExpression="SET available_seats = available_seats + :change",
            ExpressionAttributeValues={":change": seats_change},
        )

    def get_popular_routes(self) -> list[dict[str, Any]]:
        """Get popular flight routes.

        Returns:
            List of popular routes with flight counts
        """
        response = self.table.scan(
            ProjectionExpression="origin, destination",
        )

        route_counts: dict[str, int] = {}
        for item in response.get("Items", []):
            route = f"{item['origin']}-{item['destination']}"
            route_counts[route] = route_counts.get(route, 0) + 1

        return sorted(
            [{"route": k, "count": v} for k, v in route_counts.items()],
            key=lambda x: x["count"],
            reverse=True,
        )[:10]

    def _item_to_flight(self, item: dict[str, Any]) -> Flight:
        """Convert DynamoDB item to Flight model."""
        return Flight(
            flight_id=item["flight_id"],
            flight_number=item["flight_number"],
            airline=item["airline"],
            origin=item["origin"],
            destination=item["destination"],
            departure_time=datetime.fromisoformat(item["departure_time"]),
            arrival_time=datetime.fromisoformat(item["arrival_time"]),
            duration_minutes=int(item["duration_minutes"]),
            price_per_person=Decimal(str(item["price_per_person"])),
            available_seats=int(item["available_seats"]),
            cabin_class=CabinClass(item.get("cabin_class", "economy")),
        )

    def seed_sample_flights(self) -> None:
        """Seed sample flights for testing."""
        sample_flights = [
            {
                "flight_id": "FL001",
                "flight_number": "BA304",
                "airline": "British Airways",
                "origin": "LHR",
                "destination": "CDG",
                "departure_time": (datetime.now() + timedelta(days=7)).replace(
                    hour=8, minute=0
                ).isoformat(),
                "arrival_time": (datetime.now() + timedelta(days=7)).replace(
                    hour=10, minute=15
                ).isoformat(),
                "duration_minutes": 75,
                "price_per_person": Decimal("150.00"),
                "available_seats": 120,
                "cabin_class": "economy",
            },
            {
                "flight_id": "FL002",
                "flight_number": "AF1081",
                "airline": "Air France",
                "origin": "LHR",
                "destination": "CDG",
                "departure_time": (datetime.now() + timedelta(days=7)).replace(
                    hour=12, minute=30
                ).isoformat(),
                "arrival_time": (datetime.now() + timedelta(days=7)).replace(
                    hour=14, minute=45
                ).isoformat(),
                "duration_minutes": 75,
                "price_per_person": Decimal("180.00"),
                "available_seats": 85,
                "cabin_class": "economy",
            },
        ]

        for flight in sample_flights:
            self.table.put_item(Item=flight)
