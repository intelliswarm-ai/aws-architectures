"""GPS data producer Lambda handler.

Simulates GPS data from delivery trucks and sends to Kinesis.
Triggered by EventBridge on a schedule.
"""

import random
from datetime import datetime

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.models import EngineStatus, GPSCoordinate
from src.services.kinesis_service import KinesisService

logger = Logger()
tracer = Tracer()
metrics = Metrics()


# Simulated truck routes (starting positions in Switzerland)
TRUCK_ROUTES = {
    "TRK-001": {"lat": 47.3769, "lon": 8.5417, "heading": 90},   # Zurich
    "TRK-002": {"lat": 46.9480, "lon": 7.4474, "heading": 180},  # Bern
    "TRK-003": {"lat": 46.2044, "lon": 6.1432, "heading": 270},  # Geneva
    "TRK-004": {"lat": 47.5596, "lon": 7.5886, "heading": 0},    # Basel
    "TRK-005": {"lat": 46.8182, "lon": 8.2275, "heading": 45},   # Lucerne
}


def generate_gps_coordinate(truck_id: str, base_position: dict) -> GPSCoordinate:
    """Generate a simulated GPS coordinate for a truck.

    Args:
        truck_id: Truck identifier
        base_position: Base position with lat, lon, heading

    Returns:
        Simulated GPS coordinate
    """
    # Add small random movement (simulate 5-second movement at ~50 km/h)
    # At 50 km/h, truck moves ~70m in 5 seconds
    movement_factor = 0.0007  # Approximately 70m in degrees

    lat_delta = random.uniform(-movement_factor, movement_factor)
    lon_delta = random.uniform(-movement_factor, movement_factor)

    # Update heading with small variation
    heading = (base_position["heading"] + random.randint(-10, 10)) % 360

    # Simulate speed (30-80 km/h when moving, occasionally idle)
    is_idle = random.random() < 0.1  # 10% chance of being idle
    speed = 0 if is_idle else random.uniform(30, 80)
    engine_status = EngineStatus.IDLE if is_idle else EngineStatus.RUNNING

    return GPSCoordinate(
        truck_id=truck_id,
        timestamp=datetime.utcnow(),
        latitude=base_position["lat"] + lat_delta,
        longitude=base_position["lon"] + lon_delta,
        speed_kmh=round(speed, 1),
        heading=heading,
        altitude_m=random.uniform(300, 600),
        accuracy_m=random.uniform(3, 10),
        fuel_level_pct=random.uniform(20, 100),
        engine_status=engine_status,
    )


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for GPS data production.

    Generates GPS coordinates for multiple trucks and sends them to Kinesis.
    Triggered every minute by EventBridge to simulate continuous tracking.

    Args:
        event: EventBridge scheduled event
        context: Lambda context

    Returns:
        Response with success/failure counts
    """
    settings = get_settings()
    kinesis_service = KinesisService()

    # Generate number of trucks from settings or default
    num_trucks = min(settings.num_trucks, 50)  # Cap at 50 for simulation

    logger.info(
        "Starting GPS data generation",
        extra={"num_trucks": num_trucks},
    )

    # Generate coordinates for all trucks
    # In production, this would come from real IoT devices
    coordinates = []

    # Use predefined routes or generate random trucks
    truck_ids = list(TRUCK_ROUTES.keys())
    for i in range(num_trucks):
        if i < len(truck_ids):
            truck_id = truck_ids[i]
            base_position = TRUCK_ROUTES[truck_id]
        else:
            truck_id = f"TRK-{i+1:03d}"
            base_position = {
                "lat": 46.8 + random.uniform(-1, 1),
                "lon": 7.5 + random.uniform(-1, 1),
                "heading": random.randint(0, 359),
            }

        # Generate 12 coordinates per truck (simulating 1 minute of 5-sec intervals)
        for _ in range(12):
            coord = generate_gps_coordinate(truck_id, base_position)
            coordinates.append(coord)
            # Update base position for next coordinate
            base_position["lat"] = coord.latitude
            base_position["lon"] = coord.longitude
            base_position["heading"] = coord.heading

    # Send to Kinesis in batches
    batch_size = settings.batch_size
    total_success = 0
    total_failure = 0

    for i in range(0, len(coordinates), batch_size):
        batch = coordinates[i : i + batch_size]
        result = kinesis_service.put_records(batch)
        total_success += result.get("SuccessCount", 0)
        total_failure += result.get("FailureCount", 0)

    # Record metrics
    metrics.add_metric(
        name="CoordinatesGenerated",
        unit=MetricUnit.Count,
        value=len(coordinates),
    )
    metrics.add_metric(
        name="CoordinatesSent",
        unit=MetricUnit.Count,
        value=total_success,
    )
    metrics.add_metric(
        name="CoordinatesFailed",
        unit=MetricUnit.Count,
        value=total_failure,
    )

    logger.info(
        "GPS data generation completed",
        extra={
            "total_coordinates": len(coordinates),
            "success_count": total_success,
            "failure_count": total_failure,
        },
    )

    return {
        "statusCode": 200,
        "body": {
            "message": "GPS data generated successfully",
            "total_coordinates": len(coordinates),
            "success_count": total_success,
            "failure_count": total_failure,
        },
    }
