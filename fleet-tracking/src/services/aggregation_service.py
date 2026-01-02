"""Aggregation service for GPS data analytics."""

import json
from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger

from src.common.clients import get_dynamodb_client, get_s3_client
from src.common.config import get_settings
from src.common.models import AggregatedStats, EngineStatus, GPSCoordinate

if TYPE_CHECKING:
    from mypy_boto3_dynamodb import DynamoDBClient
    from mypy_boto3_s3 import S3Client

logger = Logger()

# Earth's radius in meters for distance calculations
EARTH_RADIUS_M = 6371000


class AggregationService:
    """Service for aggregating GPS data."""

    def __init__(
        self,
        dynamodb_client: "DynamoDBClient | None" = None,
        s3_client: "S3Client | None" = None,
    ):
        self.dynamodb = dynamodb_client or get_dynamodb_client()
        self.s3 = s3_client or get_s3_client()
        self.settings = get_settings()

    def aggregate_coordinates(
        self,
        coordinates: list[GPSCoordinate],
    ) -> dict[str, AggregatedStats]:
        """Aggregate GPS coordinates by truck.

        Args:
            coordinates: List of GPS coordinates

        Returns:
            Dictionary mapping truck_id to aggregated stats
        """
        if not coordinates:
            return {}

        # Group by truck
        truck_coords: dict[str, list[GPSCoordinate]] = {}
        for coord in coordinates:
            if coord.truck_id not in truck_coords:
                truck_coords[coord.truck_id] = []
            truck_coords[coord.truck_id].append(coord)

        # Calculate aggregates per truck
        results: dict[str, AggregatedStats] = {}
        for truck_id, coords in truck_coords.items():
            # Sort by timestamp
            coords.sort(key=lambda c: c.timestamp)

            stats = self._calculate_stats(truck_id, coords)
            results[truck_id] = stats

        return results

    def _calculate_stats(
        self,
        truck_id: str,
        coordinates: list[GPSCoordinate],
    ) -> AggregatedStats:
        """Calculate aggregated statistics for a single truck.

        Args:
            truck_id: Truck identifier
            coordinates: Sorted list of coordinates

        Returns:
            Aggregated statistics
        """
        if not coordinates:
            return AggregatedStats(
                truck_id=truck_id,
                period_start=datetime.utcnow(),
                period_end=datetime.utcnow(),
            )

        total_distance = 0.0
        speeds = []
        idle_time = timedelta()

        for i in range(len(coordinates)):
            coord = coordinates[i]
            speeds.append(coord.speed_kmh)

            # Calculate distance from previous point
            if i > 0:
                prev = coordinates[i - 1]
                distance = self._calculate_distance(
                    prev.latitude,
                    prev.longitude,
                    coord.latitude,
                    coord.longitude,
                )
                total_distance += distance

                # Calculate idle time
                if coord.engine_status == EngineStatus.IDLE:
                    time_diff = coord.timestamp - prev.timestamp
                    idle_time += time_diff

        return AggregatedStats(
            truck_id=truck_id,
            period_start=coordinates[0].timestamp,
            period_end=coordinates[-1].timestamp,
            total_distance_km=total_distance / 1000,
            average_speed_kmh=sum(speeds) / len(speeds) if speeds else 0,
            max_speed_kmh=max(speeds) if speeds else 0,
            idle_time_minutes=idle_time.total_seconds() / 60,
            coordinates_count=len(coordinates),
        )

    def _calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two points using Haversine formula.

        Args:
            lat1, lon1: First point
            lat2, lon2: Second point

        Returns:
            Distance in meters
        """
        import math

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

    def archive_to_s3(
        self,
        coordinates: list[GPSCoordinate],
        partition_key: str | None = None,
    ) -> str:
        """Archive GPS coordinates to S3 in JSON Lines format.

        Args:
            coordinates: Coordinates to archive
            partition_key: Optional partition key (defaults to date)

        Returns:
            S3 object key
        """
        if not coordinates:
            return ""

        if not self.settings.archive_bucket:
            logger.warning("Archive bucket not configured")
            return ""

        # Generate partition key based on date
        if partition_key is None:
            now = datetime.utcnow()
            partition_key = f"year={now.year}/month={now.month:02d}/day={now.day:02d}"

        # Create JSON Lines content
        lines = [coord.model_dump_json() for coord in coordinates]
        content = "\n".join(lines)

        # Generate object key
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        object_key = f"raw/{partition_key}/{timestamp}.jsonl"

        try:
            self.s3.put_object(
                Bucket=self.settings.archive_bucket,
                Key=object_key,
                Body=content.encode("utf-8"),
                ContentType="application/json",
            )
            logger.info(
                "Archived coordinates to S3",
                extra={
                    "bucket": self.settings.archive_bucket,
                    "key": object_key,
                    "count": len(coordinates),
                },
            )
            return object_key
        except Exception as e:
            logger.error(
                "Failed to archive to S3",
                extra={"error": str(e)},
            )
            return ""

    def archive_aggregates_to_s3(
        self,
        aggregates: dict[str, AggregatedStats],
    ) -> str:
        """Archive aggregated statistics to S3.

        Args:
            aggregates: Dictionary of aggregated stats by truck

        Returns:
            S3 object key
        """
        if not aggregates:
            return ""

        if not self.settings.archive_bucket:
            logger.warning("Archive bucket not configured")
            return ""

        # Generate content
        records = [stats.to_parquet_record() for stats in aggregates.values()]
        content = "\n".join(json.dumps(r) for r in records)

        # Generate object key
        now = datetime.utcnow()
        partition_key = f"year={now.year}/month={now.month:02d}/day={now.day:02d}"
        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")
        object_key = f"aggregates/{partition_key}/{timestamp}.jsonl"

        try:
            self.s3.put_object(
                Bucket=self.settings.archive_bucket,
                Key=object_key,
                Body=content.encode("utf-8"),
                ContentType="application/json",
            )
            logger.info(
                "Archived aggregates to S3",
                extra={
                    "bucket": self.settings.archive_bucket,
                    "key": object_key,
                    "count": len(aggregates),
                },
            )
            return object_key
        except Exception as e:
            logger.error(
                "Failed to archive aggregates to S3",
                extra={"error": str(e)},
            )
            return ""
