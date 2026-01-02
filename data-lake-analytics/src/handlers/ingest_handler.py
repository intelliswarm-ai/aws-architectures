"""Lambda handler for data ingestion into the data lake.

This handler receives JSON documents and writes them to S3 in
partitioned format for optimal Athena query performance.
"""

import json
import logging
from datetime import datetime
from typing import Any

from ..common.config import settings
from ..common.models import EventDocument, PartitionSpec
from ..services import get_s3_service

logger = logging.getLogger()
logger.setLevel(settings.log_level)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle data ingestion requests.

    Supports multiple event sources:
    - Direct invocation with documents
    - API Gateway events
    - Kinesis Data Streams events
    - S3 events (for reprocessing)

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Response with ingestion results
    """
    logger.info(f"Ingestion handler invoked with event type: {_get_event_type(event)}")

    try:
        event_type = _get_event_type(event)

        if event_type == "api_gateway":
            return _handle_api_request(event)
        elif event_type == "kinesis":
            return _handle_kinesis_records(event)
        elif event_type == "direct":
            return _handle_direct_invocation(event)
        else:
            return _error_response(400, f"Unsupported event type: {event_type}")

    except Exception as e:
        logger.exception(f"Ingestion failed: {e}")
        return _error_response(500, str(e))


def _get_event_type(event: dict[str, Any]) -> str:
    """Determine event source type."""
    if "httpMethod" in event or "requestContext" in event:
        return "api_gateway"
    elif "Records" in event:
        records = event["Records"]
        if records and "kinesis" in records[0]:
            return "kinesis"
        elif records and "s3" in records[0]:
            return "s3"
    return "direct"


def _handle_api_request(event: dict[str, Any]) -> dict[str, Any]:
    """Handle API Gateway request for data ingestion."""
    s3_service = get_s3_service()

    body = event.get("body", "{}")
    if event.get("isBase64Encoded"):
        import base64

        body = base64.b64decode(body).decode("utf-8")

    data = json.loads(body)
    documents = data.get("documents", [])

    if not documents:
        return _api_response(400, {"error": "No documents provided"})

    # Parse and validate documents
    event_docs = []
    for doc in documents:
        try:
            event_docs.append(EventDocument(**doc))
        except Exception as e:
            logger.warning(f"Invalid document skipped: {e}")

    if not event_docs:
        return _api_response(400, {"error": "No valid documents"})

    # Determine partition (use first document timestamp or current time)
    partition_time = event_docs[0].timestamp
    partition = PartitionSpec.from_datetime(partition_time)

    # Write to S3
    result = s3_service.write_json_documents(event_docs, partition)

    return _api_response(
        200,
        {
            "status": "success",
            "records_written": result.records_written,
            "bytes_written": result.bytes_written,
            "s3_location": f"s3://{result.bucket}/{result.s3_key}",
            "partition": result.partition.path,
        },
    )


def _handle_kinesis_records(event: dict[str, Any]) -> dict[str, Any]:
    """Handle Kinesis Data Stream records."""
    import base64

    s3_service = get_s3_service()

    records = event.get("Records", [])
    event_docs = []

    for record in records:
        kinesis_data = record["kinesis"]["data"]
        decoded_data = base64.b64decode(kinesis_data).decode("utf-8")

        try:
            doc_data = json.loads(decoded_data)
            event_docs.append(EventDocument(**doc_data))
        except Exception as e:
            logger.warning(f"Failed to parse Kinesis record: {e}")

    if not event_docs:
        return {
            "statusCode": 200,
            "body": json.dumps({"status": "no_valid_records", "total_records": len(records)}),
        }

    # Group by partition for efficient writes
    partitioned_docs: dict[str, list[EventDocument]] = {}
    for doc in event_docs:
        partition = PartitionSpec.from_datetime(doc.timestamp)
        key = partition.path
        if key not in partitioned_docs:
            partitioned_docs[key] = []
        partitioned_docs[key].append(doc)

    # Write each partition batch
    total_written = 0
    total_bytes = 0
    for partition_path, docs in partitioned_docs.items():
        partition = PartitionSpec(
            year=partition_path.split("/")[0].split("=")[1],
            month=partition_path.split("/")[1].split("=")[1],
            day=partition_path.split("/")[2].split("=")[1],
            hour=partition_path.split("/")[3].split("=")[1] if len(partition_path.split("/")) > 3 else None,
        )
        result = s3_service.write_json_documents(docs, partition)
        total_written += result.records_written
        total_bytes += result.bytes_written

    logger.info(f"Ingested {total_written} records ({total_bytes} bytes) from Kinesis")

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "status": "success",
                "records_processed": len(records),
                "records_written": total_written,
                "bytes_written": total_bytes,
                "partitions": len(partitioned_docs),
            }
        ),
    }


def _handle_direct_invocation(event: dict[str, Any]) -> dict[str, Any]:
    """Handle direct Lambda invocation with documents."""
    s3_service = get_s3_service()

    documents = event.get("documents", [])
    if not documents:
        return {"status": "error", "message": "No documents provided"}

    # Parse documents
    event_docs = []
    for doc in documents:
        try:
            event_docs.append(EventDocument(**doc))
        except Exception as e:
            logger.warning(f"Invalid document: {e}")

    if not event_docs:
        return {"status": "error", "message": "No valid documents"}

    # Use provided partition or derive from documents
    partition = None
    if "partition" in event:
        partition = PartitionSpec(**event["partition"])
    else:
        partition = PartitionSpec.from_datetime(event_docs[0].timestamp)

    result = s3_service.write_json_documents(event_docs, partition)

    return {
        "status": "success",
        "records_written": result.records_written,
        "bytes_written": result.bytes_written,
        "s3_key": result.s3_key,
        "bucket": result.bucket,
        "partition": result.partition.path,
    }


def _api_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Create API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }


def _error_response(status_code: int, message: str) -> dict[str, Any]:
    """Create error response."""
    return _api_response(status_code, {"error": message})
