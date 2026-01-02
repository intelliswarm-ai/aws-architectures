"""Geofence service for GPS boundary detection."""

import math
import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger

from src.common.clients import get_dynamodb_client, get_sns_client
from src.common.config import get_settings
from src.common.exceptions import GeofenceError
from src.common.models import (
    AlertType,
    Geofence,
    GeofenceAlert,
    GeofenceType,
    GPSCoordinate,
)

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient
    from mypy_boto3_sns import SNSClient

logger = Logger()

# Earth's radius in meters
EARTH_RADIUS_M = 6371000


class GeofenceService:
    """Service for geofence operations."""

    def __init__(
        self,
        dynamodb_client: "DynamoDBClient | None" = None,
        sns_client: "SNSClient | None" = None,
    ):
        self.dynamodb = dynamodb_client or get_dynamodb_client()
        self.sns = sns_client or get_sns_client()
        self.settings = get_settings()
        self._geofences_cache: dict[str, Geofence] = {}
        self._truck_states: dict[str, dict[str, bool]] = {}  # truck_id -> geofence_id -> inside

    def load_geofences(self) -> list[Geofence]:
        """Load all active geofences from DynamoDB.

        Returns:
            List of active geofences
        """
        try:
            response = self.dynamodb.scan(
                TableName=self.settings.geofences_table,
                FilterExpression="active = :active",
                ExpressionAttributeValues={":active": {"BOOL": True}},
            )

            geofences = []
            for item in response.get("Items", []):
                geofence = Geofence(
                    geofence_id=item["geofence_id"]["S"],
                    name=item["name"]["S"],
                    geofence_type=GeofenceType(item.get("geofence_type", {}).get("S", "circle")),
                    center_latitude=float(item["center_latitude"]["N"]),
                    center_longitude=float(item["center_longitude"]["N"]),
                    radius_meters=float(item.get("radius_meters", {}).get("N", 500)),
                    alert_on=AlertType(item.get("alert_on", {}).get("S", "both")),
                    active=True,
                )
                geofences.append(geofence)
                self._geofences_cache[geofence.geofence_id] = geofence

            logger.info("Loaded geofences", extra={"count": len(geofences)})
            return geofences
        except Exception as e:
            raise GeofenceError(
                "Failed to load geofences",
                details={"error": str(e)},
            ) from e

    def check_coordinate(
        self,
        coordinate: GPSCoordinate,
    ) -> list[GeofenceAlert]:
        """Check if a coordinate triggers any geofence alerts.

        Args:
            coordinate: GPS coordinate to check

        Returns:
            List of triggered alerts
        """
        if not self._geofences_cache:
            self.load_geofences()

        alerts = []
        truck_id = coordinate.truck_id

        # Initialize truck state if not exists
        if truck_id not in self._truck_states:
            self._truck_states[truck_id] = {}

        for geofence_id, geofence in self._geofences_cache.items():
            is_inside = self._is_inside_geofence(coordinate, geofence)
            was_inside = self._truck_states[truck_id].get(geofence_id, None)

            # Detect state change
            if was_inside is not None and was_inside != is_inside:
                alert_type = "enter" if is_inside else "exit"

                # Check if we should alert for this type
                should_alert = (
                    geofence.alert_on == AlertType.BOTH
                    or (geofence.alert_on == AlertType.ENTER and alert_type == "enter")
                    or (geofence.alert_on == AlertType.EXIT and alert_type == "exit")
                )

                if should_alert:
                    alert = GeofenceAlert(
                        alert_id=str(uuid.uuid4()),
                        truck_id=truck_id,
                        geofence_id=geofence_id,
                        geofence_name=geofence.name,
                        alert_type=alert_type,
                        timestamp=coordinate.timestamp,
                        latitude=coordinate.latitude,
                        longitude=coordinate.longitude,
                    )
                    alerts.append(alert)
                    logger.info(
                        "Geofence alert triggered",
                        extra={
                            "alert_id": alert.alert_id,
                            "truck_id": truck_id,
                            "geofence_name": geofence.name,
                            "alert_type": alert_type,
                        },
                    )

            # Update state
            self._truck_states[truck_id][geofence_id] = is_inside

        return alerts

    def _is_inside_geofence(
        self,
        coordinate: GPSCoordinate,
        geofence: Geofence,
    ) -> bool:
        """Check if coordinate is inside a geofence.

        Args:
            coordinate: GPS coordinate
            geofence: Geofence to check

        Returns:
            True if inside, False otherwise
        """
        if geofence.geofence_type == GeofenceType.CIRCLE:
            return self._is_inside_circle(coordinate, geofence)
        else:
            return self._is_inside_polygon(coordinate, geofence)

    def _is_inside_circle(
        self,
        coordinate: GPSCoordinate,
        geofence: Geofence,
    ) -> bool:
        """Check if coordinate is inside a circular geofence.

        Uses Haversine formula for distance calculation.
        """
        distance = self._haversine_distance(
            coordinate.latitude,
            coordinate.longitude,
            geofence.center_latitude,
            geofence.center_longitude,
        )
        return distance <= geofence.radius_meters

    def _is_inside_polygon(
        self,
        coordinate: GPSCoordinate,
        geofence: Geofence,
    ) -> bool:
        """Check if coordinate is inside a polygon geofence.

        Uses ray casting algorithm.
        """
        if not geofence.polygon_coordinates:
            return False

        x, y = coordinate.latitude, coordinate.longitude
        n = len(geofence.polygon_coordinates)
        inside = False

        p1x, p1y = geofence.polygon_coordinates[0]
        for i in range(1, n + 1):
            p2x, p2y = geofence.polygon_coordinates[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def _haversine_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two points using Haversine formula.

        Args:
            lat1, lon1: First point coordinates
            lat2, lon2: Second point coordinates

        Returns:
            Distance in meters
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_lat / 2) ** 2
            + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return EARTH_RADIUS_M * c

    def publish_alert(self, alert: GeofenceAlert) -> None:
        """Publish geofence alert to SNS.

        Args:
            alert: Alert to publish
        """
        if not self.settings.alerts_topic_arn:
            logger.warning("SNS topic ARN not configured, skipping alert publish")
            return

        try:
            self.sns.publish(
                TopicArn=self.settings.alerts_topic_arn,
                Message=alert.to_sns_message(),
                Subject=f"Geofence Alert: {alert.truck_id} {alert.alert_type} {alert.geofence_name}",
                MessageAttributes={
                    "truck_id": {"DataType": "String", "StringValue": alert.truck_id},
                    "alert_type": {"DataType": "String", "StringValue": alert.alert_type},
                    "geofence_id": {"DataType": "String", "StringValue": alert.geofence_id},
                },
            )
            logger.info(
                "Published geofence alert",
                extra={"alert_id": alert.alert_id},
            )
        except Exception as e:
            logger.error(
                "Failed to publish alert",
                extra={"alert_id": alert.alert_id, "error": str(e)},
            )
