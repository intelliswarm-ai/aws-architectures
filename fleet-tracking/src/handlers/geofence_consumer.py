"""Geofence consumer Lambda handler.

Processes GPS coordinates from Kinesis and checks for geofence violations.
Publishes alerts to SNS when trucks enter or exit defined geofences.
"""

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.services.geofence_service import GeofenceService
from src.services.kinesis_service import KinesisService

logger = Logger()
tracer = Tracer()
metrics = Metrics()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for geofence consumer.

    Processes GPS coordinates from Kinesis, checks against defined geofences,
    and publishes alerts to SNS when boundaries are crossed.

    Args:
        event: Kinesis stream event with GPS records
        context: Lambda context

    Returns:
        Response with processing results and alerts triggered
    """
    kinesis_service = KinesisService()
    geofence_service = GeofenceService()

    records = event.get("Records", [])
    if not records:
        logger.info("No records to process")
        return {"statusCode": 200, "body": {"processed": 0}}

    logger.info(
        "Processing Kinesis records for geofence checks",
        extra={"record_count": len(records)},
    )

    # Parse Kinesis records
    coordinates = kinesis_service.parse_kinesis_records(records)

    if not coordinates:
        logger.warning("No valid coordinates parsed from records")
        return {"statusCode": 200, "body": {"processed": 0, "valid": 0}}

    # Sort coordinates by timestamp to ensure correct state tracking
    coordinates.sort(key=lambda c: (c.truck_id, c.timestamp))

    # Check each coordinate against geofences
    all_alerts = []
    coordinates_checked = 0

    for coord in coordinates:
        alerts = geofence_service.check_coordinate(coord)
        all_alerts.extend(alerts)
        coordinates_checked += 1

        # Publish each alert to SNS
        for alert in alerts:
            geofence_service.publish_alert(alert)

    # Record metrics
    metrics.add_metric(
        name="RecordsProcessed",
        unit=MetricUnit.Count,
        value=len(records),
    )
    metrics.add_metric(
        name="CoordinatesChecked",
        unit=MetricUnit.Count,
        value=coordinates_checked,
    )
    metrics.add_metric(
        name="AlertsTriggered",
        unit=MetricUnit.Count,
        value=len(all_alerts),
    )

    # Log alert summary
    if all_alerts:
        enter_alerts = sum(1 for a in all_alerts if a.alert_type == "enter")
        exit_alerts = sum(1 for a in all_alerts if a.alert_type == "exit")

        logger.info(
            "Geofence alerts triggered",
            extra={
                "total_alerts": len(all_alerts),
                "enter_alerts": enter_alerts,
                "exit_alerts": exit_alerts,
                "affected_trucks": len(set(a.truck_id for a in all_alerts)),
            },
        )

    logger.info(
        "Geofence consumer processing completed",
        extra={
            "records_processed": len(records),
            "coordinates_checked": coordinates_checked,
            "alerts_triggered": len(all_alerts),
        },
    )

    return {
        "statusCode": 200,
        "body": {
            "records_processed": len(records),
            "coordinates_checked": coordinates_checked,
            "alerts_triggered": len(all_alerts),
            "alerts": [
                {
                    "alert_id": a.alert_id,
                    "truck_id": a.truck_id,
                    "geofence_name": a.geofence_name,
                    "alert_type": a.alert_type,
                }
                for a in all_alerts
            ],
        },
    }
