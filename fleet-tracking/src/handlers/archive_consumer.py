"""Archive consumer Lambda handler.

Processes GPS coordinates from Kinesis and archives them to S3.
Also calculates aggregated statistics for reporting.
"""

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.services.aggregation_service import AggregationService
from src.services.kinesis_service import KinesisService

logger = Logger()
tracer = Tracer()
metrics = Metrics()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for archive consumer.

    Processes GPS coordinates from Kinesis, archives raw data to S3,
    and calculates aggregated statistics for reporting.

    Args:
        event: Kinesis stream event with GPS records
        context: Lambda context

    Returns:
        Response with processing results
    """
    kinesis_service = KinesisService()
    aggregation_service = AggregationService()

    records = event.get("Records", [])
    if not records:
        logger.info("No records to process")
        return {"statusCode": 200, "body": {"processed": 0}}

    logger.info(
        "Processing Kinesis records for archival",
        extra={"record_count": len(records)},
    )

    # Parse Kinesis records
    coordinates = kinesis_service.parse_kinesis_records(records)

    if not coordinates:
        logger.warning("No valid coordinates parsed from records")
        return {"statusCode": 200, "body": {"processed": 0, "valid": 0}}

    # Archive raw coordinates to S3
    raw_object_key = aggregation_service.archive_to_s3(coordinates)

    # Calculate aggregated statistics
    aggregates = aggregation_service.aggregate_coordinates(coordinates)

    # Archive aggregates to S3
    aggregates_object_key = aggregation_service.archive_aggregates_to_s3(aggregates)

    # Calculate summary statistics for logging
    total_distance = sum(a.total_distance_km for a in aggregates.values())
    avg_speed = (
        sum(a.average_speed_kmh for a in aggregates.values()) / len(aggregates)
        if aggregates
        else 0
    )
    max_speed = max((a.max_speed_kmh for a in aggregates.values()), default=0)

    # Record metrics
    metrics.add_metric(
        name="RecordsProcessed",
        unit=MetricUnit.Count,
        value=len(records),
    )
    metrics.add_metric(
        name="CoordinatesArchived",
        unit=MetricUnit.Count,
        value=len(coordinates),
    )
    metrics.add_metric(
        name="TrucksAggregated",
        unit=MetricUnit.Count,
        value=len(aggregates),
    )
    metrics.add_metric(
        name="TotalDistanceKm",
        unit=MetricUnit.Count,
        value=round(total_distance, 2),
    )

    logger.info(
        "Archive consumer processing completed",
        extra={
            "records_processed": len(records),
            "coordinates_archived": len(coordinates),
            "trucks_aggregated": len(aggregates),
            "raw_s3_key": raw_object_key,
            "aggregates_s3_key": aggregates_object_key,
            "total_distance_km": round(total_distance, 2),
            "avg_speed_kmh": round(avg_speed, 2),
            "max_speed_kmh": round(max_speed, 2),
        },
    )

    return {
        "statusCode": 200,
        "body": {
            "records_processed": len(records),
            "coordinates_archived": len(coordinates),
            "trucks_aggregated": len(aggregates),
            "raw_s3_key": raw_object_key,
            "aggregates_s3_key": aggregates_object_key,
            "summary": {
                "total_distance_km": round(total_distance, 2),
                "average_speed_kmh": round(avg_speed, 2),
                "max_speed_kmh": round(max_speed, 2),
            },
        },
    }
