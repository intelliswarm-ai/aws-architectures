"""Archive Consumer Lambda Handler.

Archives all SMS events to S3 for long-term storage and compliance.
Data is stored in Parquet format partitioned by date.
"""

import gzip
import json
from datetime import datetime
from typing import Any
from io import BytesIO

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent
from aws_lambda_powertools.utilities.typing import LambdaContext

from services.kinesis_service import KinesisService
from common.clients import get_s3_client
from common.config import settings
from common.models import ArchiveRecord

logger = Logger()
tracer = Tracer()
metrics = Metrics()

kinesis_service = KinesisService()
s3_client = get_s3_client()


@tracer.capture_method
def create_archive_record(data: dict) -> ArchiveRecord | None:
    """Create an archive record from raw event data."""
    try:
        event_type = data.get("event_type", "")
        if not event_type.startswith("_SMS"):
            return None

        attributes = data.get("attributes", {})
        metrics_data = data.get("metrics", {})
        client = data.get("client", {})

        return ArchiveRecord(
            event_type=event_type,
            event_timestamp=data.get("event_timestamp", datetime.utcnow().isoformat()),
            subscriber_id=client.get("client_id", ""),
            phone_number=attributes.get("destination_phone_number", "")
            or attributes.get("origination_number", ""),
            message_id=attributes.get("message_id", ""),
            campaign_id=attributes.get("campaign_id", ""),
            journey_id=attributes.get("journey_id", ""),
            record_status=attributes.get("record_status", ""),
            message_type=attributes.get("message_type", ""),
            country_code=attributes.get("iso_country_code", ""),
            price_millicents=metrics_data.get("price_in_millicents_usd", 0),
            response_text=attributes.get("message_body"),
        )
    except Exception as e:
        logger.warning(f"Failed to create archive record: {e}")
        return None


@tracer.capture_method
def upload_to_s3(records: list[ArchiveRecord], batch_timestamp: datetime) -> str:
    """Upload records to S3 in JSONL format (gzipped)."""
    if not records:
        return ""

    # Create S3 key with date partitioning
    date_prefix = batch_timestamp.strftime("year=%Y/month=%m/day=%d")
    timestamp_suffix = batch_timestamp.strftime("%H%M%S%f")
    s3_key = f"events/{date_prefix}/events_{timestamp_suffix}.jsonl.gz"

    # Create JSONL content
    lines = [json.dumps(record.to_parquet_dict()) for record in records]
    content = "\n".join(lines)

    # Compress with gzip
    buffer = BytesIO()
    with gzip.GzipFile(fileobj=buffer, mode="wb") as gz:
        gz.write(content.encode("utf-8"))
    buffer.seek(0)

    # Upload to S3
    s3_client.put_object(
        Bucket=settings.archive_bucket,
        Key=s3_key,
        Body=buffer.getvalue(),
        ContentType="application/x-ndjson",
        ContentEncoding="gzip",
        Metadata={
            "record_count": str(len(records)),
            "batch_timestamp": batch_timestamp.isoformat(),
        },
    )

    logger.info(
        "Uploaded archive batch to S3",
        extra={
            "s3_key": s3_key,
            "record_count": len(records),
        },
    )

    return s3_key


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict, context: LambdaContext) -> dict:
    """Lambda handler for archiving SMS events to S3."""
    kinesis_event = KinesisStreamEvent(event)
    batch_timestamp = datetime.utcnow()

    logger.info(
        "Processing events for archive",
        extra={"record_count": len(kinesis_event.records)},
    )

    archive_records: list[ArchiveRecord] = []
    failed_count = 0

    for record in kinesis_event.records:
        try:
            data = kinesis_service.decode_record({"kinesis": record.raw_event["kinesis"]})
            archive_record = create_archive_record(data)

            if archive_record:
                archive_records.append(archive_record)

        except Exception as e:
            logger.warning(f"Failed to process record for archive: {e}")
            failed_count += 1

    # Upload batch to S3
    s3_key = ""
    if archive_records:
        s3_key = upload_to_s3(archive_records, batch_timestamp)

        metrics.add_metric(
            name="RecordsArchived",
            unit=MetricUnit.Count,
            value=len(archive_records),
        )

    if failed_count > 0:
        metrics.add_metric(
            name="ArchiveFailures",
            unit=MetricUnit.Count,
            value=failed_count,
        )

    logger.info(
        "Completed archive processing",
        extra={
            "archived": len(archive_records),
            "failed": failed_count,
            "s3_key": s3_key,
        },
    )

    return {
        "statusCode": 200,
        "body": {
            "archived": len(archive_records),
            "failed": failed_count,
            "s3_key": s3_key,
        },
    }
