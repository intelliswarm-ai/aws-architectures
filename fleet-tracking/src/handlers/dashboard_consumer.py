"""Dashboard consumer Lambda handler.

Processes GPS coordinates from Kinesis and updates DynamoDB with latest positions.
This enables real-time fleet tracking dashboards.
"""

from datetime import datetime, timedelta

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_dynamodb_client
from src.common.config import get_settings
from src.common.models import TruckPosition
from src.services.kinesis_service import KinesisService

logger = Logger()
tracer = Tracer()
metrics = Metrics()


@tracer.capture_method
def update_truck_position(
    dynamodb_client,
    table_name: str,
    position: TruckPosition,
) -> bool:
    """Update truck position in DynamoDB.

    Uses conditional update to ensure we only store the latest position.

    Args:
        dynamodb_client: DynamoDB client
        table_name: DynamoDB table name
        position: Truck position to update

    Returns:
        True if update succeeded, False otherwise
    """
    try:
        dynamodb_client.put_item(
            TableName=table_name,
            Item=position.to_dynamodb_item(),
            ConditionExpression=(
                "attribute_not_exists(truck_id) OR last_update < :new_update"
            ),
            ExpressionAttributeValues={
                ":new_update": {"S": position.last_update.isoformat()},
            },
        )
        return True
    except dynamodb_client.exceptions.ConditionalCheckFailedException:
        # Position was already updated with a newer timestamp
        logger.debug(
            "Skipping older position update",
            extra={"truck_id": position.truck_id},
        )
        return False
    except Exception as e:
        logger.error(
            "Failed to update truck position",
            extra={"truck_id": position.truck_id, "error": str(e)},
        )
        return False


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for dashboard consumer.

    Processes GPS coordinates from Kinesis and updates DynamoDB
    with the latest position for each truck.

    Args:
        event: Kinesis stream event with GPS records
        context: Lambda context

    Returns:
        Response with processing results
    """
    settings = get_settings()
    kinesis_service = KinesisService()
    dynamodb = get_dynamodb_client()

    records = event.get("Records", [])
    if not records:
        logger.info("No records to process")
        return {"statusCode": 200, "body": {"processed": 0}}

    logger.info(
        "Processing Kinesis records",
        extra={"record_count": len(records)},
    )

    # Parse Kinesis records
    coordinates = kinesis_service.parse_kinesis_records(records)

    if not coordinates:
        logger.warning("No valid coordinates parsed from records")
        return {"statusCode": 200, "body": {"processed": 0, "valid": 0}}

    # Group by truck and keep only the latest coordinate per truck
    latest_by_truck: dict[str, TruckPosition] = {}
    for coord in coordinates:
        truck_id = coord.truck_id

        # Calculate TTL (24 hours from now)
        ttl = int((datetime.utcnow() + timedelta(hours=24)).timestamp())

        position = TruckPosition(
            truck_id=truck_id,
            last_update=coord.timestamp,
            latitude=coord.latitude,
            longitude=coord.longitude,
            speed_kmh=coord.speed_kmh,
            heading=coord.heading,
            engine_status=coord.engine_status,
            fuel_level_pct=coord.fuel_level_pct,
            ttl=ttl,
        )

        # Keep only the latest position per truck
        if truck_id not in latest_by_truck:
            latest_by_truck[truck_id] = position
        elif position.last_update > latest_by_truck[truck_id].last_update:
            latest_by_truck[truck_id] = position

    # Update DynamoDB with latest positions
    success_count = 0
    failure_count = 0

    for position in latest_by_truck.values():
        if update_truck_position(dynamodb, settings.positions_table, position):
            success_count += 1
        else:
            failure_count += 1

    # Record metrics
    metrics.add_metric(
        name="RecordsProcessed",
        unit=MetricUnit.Count,
        value=len(records),
    )
    metrics.add_metric(
        name="CoordinatesParsed",
        unit=MetricUnit.Count,
        value=len(coordinates),
    )
    metrics.add_metric(
        name="PositionsUpdated",
        unit=MetricUnit.Count,
        value=success_count,
    )
    metrics.add_metric(
        name="UniquesTrucks",
        unit=MetricUnit.Count,
        value=len(latest_by_truck),
    )

    logger.info(
        "Dashboard consumer processing completed",
        extra={
            "records_processed": len(records),
            "coordinates_parsed": len(coordinates),
            "unique_trucks": len(latest_by_truck),
            "positions_updated": success_count,
            "update_failures": failure_count,
        },
    )

    return {
        "statusCode": 200,
        "body": {
            "records_processed": len(records),
            "coordinates_parsed": len(coordinates),
            "positions_updated": success_count,
            "update_failures": failure_count,
        },
    }
