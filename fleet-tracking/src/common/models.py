"""Data models for the GPS tracking system."""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class EngineStatus(str, Enum):
    """Engine status enum."""

    RUNNING = "running"
    IDLE = "idle"
    OFF = "off"


class GeofenceType(str, Enum):
    """Geofence type enum."""

    CIRCLE = "circle"
    POLYGON = "polygon"


class AlertType(str, Enum):
    """Geofence alert type enum."""

    ENTER = "enter"
    EXIT = "exit"
    BOTH = "both"


class GPSCoordinate(BaseModel):
    """GPS coordinate data from a delivery truck."""

    truck_id: str = Field(..., description="Unique truck identifier")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the GPS reading",
    )
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in degrees")
    speed_kmh: float = Field(default=0, ge=0, description="Speed in km/h")
    heading: int = Field(default=0, ge=0, le=360, description="Heading in degrees")
    altitude_m: float = Field(default=0, description="Altitude in meters")
    accuracy_m: float = Field(default=5, ge=0, description="GPS accuracy in meters")
    fuel_level_pct: float = Field(
        default=100,
        ge=0,
        le=100,
        description="Fuel level percentage",
    )
    engine_status: EngineStatus = Field(
        default=EngineStatus.RUNNING,
        description="Engine status",
    )

    def to_kinesis_record(self) -> dict:
        """Convert to Kinesis record format."""
        return {
            "Data": self.model_dump_json().encode("utf-8"),
            "PartitionKey": self.truck_id,
        }

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


class TruckPosition(BaseModel):
    """Current position of a truck (stored in DynamoDB)."""

    truck_id: str = Field(..., description="Unique truck identifier")
    last_update: datetime = Field(..., description="Last update timestamp")
    latitude: float = Field(..., description="Current latitude")
    longitude: float = Field(..., description="Current longitude")
    speed_kmh: float = Field(default=0, description="Current speed")
    heading: int = Field(default=0, description="Current heading")
    engine_status: EngineStatus = Field(
        default=EngineStatus.RUNNING,
        description="Engine status",
    )
    fuel_level_pct: float = Field(default=100, description="Fuel level")
    ttl: int = Field(default=0, description="TTL for DynamoDB")

    def to_dynamodb_item(self) -> dict:
        """Convert to DynamoDB item format."""
        return {
            "truck_id": {"S": self.truck_id},
            "last_update": {"S": self.last_update.isoformat()},
            "latitude": {"N": str(self.latitude)},
            "longitude": {"N": str(self.longitude)},
            "speed_kmh": {"N": str(self.speed_kmh)},
            "heading": {"N": str(self.heading)},
            "engine_status": {"S": self.engine_status.value},
            "fuel_level_pct": {"N": str(self.fuel_level_pct)},
            "ttl": {"N": str(self.ttl)},
        }


class Geofence(BaseModel):
    """Geofence definition."""

    geofence_id: str = Field(..., description="Unique geofence identifier")
    name: str = Field(..., description="Geofence name")
    geofence_type: GeofenceType = Field(
        default=GeofenceType.CIRCLE,
        description="Type of geofence",
    )
    center_latitude: float = Field(..., description="Center latitude for circle")
    center_longitude: float = Field(..., description="Center longitude for circle")
    radius_meters: float = Field(default=500, description="Radius in meters for circle")
    polygon_coordinates: list[tuple[float, float]] = Field(
        default_factory=list,
        description="Polygon coordinates (lat, lon) pairs",
    )
    alert_on: AlertType = Field(
        default=AlertType.BOTH,
        description="When to trigger alerts",
    )
    active: bool = Field(default=True, description="Whether geofence is active")


class GeofenceAlert(BaseModel):
    """Geofence alert event."""

    alert_id: str = Field(..., description="Unique alert identifier")
    truck_id: str = Field(..., description="Truck that triggered the alert")
    geofence_id: str = Field(..., description="Geofence that was triggered")
    geofence_name: str = Field(..., description="Name of the geofence")
    alert_type: Literal["enter", "exit"] = Field(
        ...,
        description="Type of alert",
    )
    timestamp: datetime = Field(..., description="When the alert occurred")
    latitude: float = Field(..., description="Truck latitude at alert time")
    longitude: float = Field(..., description="Truck longitude at alert time")

    def to_sns_message(self) -> str:
        """Convert to SNS message format."""
        return self.model_dump_json()


class AggregatedStats(BaseModel):
    """Aggregated statistics for a truck over a time period."""

    truck_id: str = Field(..., description="Truck identifier")
    period_start: datetime = Field(..., description="Start of aggregation period")
    period_end: datetime = Field(..., description="End of aggregation period")
    total_distance_km: float = Field(default=0, description="Total distance traveled")
    average_speed_kmh: float = Field(default=0, description="Average speed")
    max_speed_kmh: float = Field(default=0, description="Maximum speed")
    idle_time_minutes: float = Field(default=0, description="Time spent idle")
    coordinates_count: int = Field(default=0, description="Number of GPS readings")

    def to_parquet_record(self) -> dict:
        """Convert to Parquet-compatible dict."""
        return {
            "truck_id": self.truck_id,
            "period_start": self.period_start.isoformat(),
            "period_end": self.period_end.isoformat(),
            "total_distance_km": self.total_distance_km,
            "average_speed_kmh": self.average_speed_kmh,
            "max_speed_kmh": self.max_speed_kmh,
            "idle_time_minutes": self.idle_time_minutes,
            "coordinates_count": self.coordinates_count,
        }
