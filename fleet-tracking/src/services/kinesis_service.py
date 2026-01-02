"""Kinesis service for GPS data streaming."""

import json
from typing import TYPE_CHECKING

from aws_lambda_powertools import Logger

from src.common.clients import get_kinesis_client
from src.common.config import get_settings
from src.common.exceptions import KinesisError
from src.common.models import GPSCoordinate

if TYPE_CHECKING:
    from mypy_boto3_kinesis import KinesisClient

logger = Logger()


class KinesisService:
    """Service for Kinesis operations."""

    def __init__(self, client: "KinesisClient | None" = None):
        self.client = client or get_kinesis_client()
        self.settings = get_settings()

    def put_record(self, coordinate: GPSCoordinate) -> dict:
        """Put a single GPS coordinate record to Kinesis.

        Args:
            coordinate: GPS coordinate to send

        Returns:
            Kinesis put record response

        Raises:
            KinesisError: If the put operation fails
        """
        try:
            response = self.client.put_record(
                StreamName=self.settings.stream_name,
                Data=coordinate.model_dump_json().encode("utf-8"),
                PartitionKey=coordinate.truck_id,
            )
            logger.debug(
                "Put record to Kinesis",
                extra={
                    "truck_id": coordinate.truck_id,
                    "shard_id": response.get("ShardId"),
                    "sequence_number": response.get("SequenceNumber"),
                },
            )
            return response
        except Exception as e:
            raise KinesisError(
                f"Failed to put record for truck {coordinate.truck_id}",
                details={"error": str(e)},
            ) from e

    def put_records(self, coordinates: list[GPSCoordinate]) -> dict:
        """Put multiple GPS coordinate records to Kinesis.

        Args:
            coordinates: List of GPS coordinates to send

        Returns:
            Kinesis put records response with success/failure counts

        Raises:
            KinesisError: If the put operation fails
        """
        if not coordinates:
            return {"SuccessCount": 0, "FailureCount": 0}

        records = [
            {
                "Data": coord.model_dump_json().encode("utf-8"),
                "PartitionKey": coord.truck_id,
            }
            for coord in coordinates
        ]

        try:
            response = self.client.put_records(
                StreamName=self.settings.stream_name,
                Records=records,
            )

            failed_count = response.get("FailedRecordCount", 0)
            success_count = len(records) - failed_count

            logger.info(
                "Put records to Kinesis",
                extra={
                    "total_records": len(records),
                    "success_count": success_count,
                    "failed_count": failed_count,
                },
            )

            # Retry failed records
            if failed_count > 0:
                self._retry_failed_records(coordinates, response.get("Records", []))

            return {
                "SuccessCount": success_count,
                "FailureCount": failed_count,
                "Records": response.get("Records", []),
            }
        except Exception as e:
            raise KinesisError(
                f"Failed to put {len(coordinates)} records",
                details={"error": str(e)},
            ) from e

    def _retry_failed_records(
        self,
        coordinates: list[GPSCoordinate],
        results: list[dict],
    ) -> None:
        """Retry failed records with exponential backoff.

        Args:
            coordinates: Original coordinates
            results: Results from put_records call
        """
        failed_coordinates = [
            coord
            for coord, result in zip(coordinates, results)
            if result.get("ErrorCode")
        ]

        if failed_coordinates:
            logger.warning(
                "Retrying failed records",
                extra={"count": len(failed_coordinates)},
            )
            # In production, implement exponential backoff
            # For now, just log the failure
            for coord in failed_coordinates:
                logger.error(
                    "Failed to send coordinate",
                    extra={"truck_id": coord.truck_id},
                )

    def parse_kinesis_records(self, records: list[dict]) -> list[GPSCoordinate]:
        """Parse Kinesis records from Lambda event.

        Args:
            records: Kinesis records from Lambda event

        Returns:
            List of parsed GPS coordinates
        """
        coordinates = []
        for record in records:
            try:
                # Kinesis data is base64 encoded in Lambda events
                import base64

                data = base64.b64decode(record["kinesis"]["data"])
                coord_dict = json.loads(data.decode("utf-8"))
                coordinate = GPSCoordinate(**coord_dict)
                coordinates.append(coordinate)
            except Exception as e:
                logger.error(
                    "Failed to parse Kinesis record",
                    extra={
                        "error": str(e),
                        "sequence_number": record.get("kinesis", {}).get(
                            "sequenceNumber"
                        ),
                    },
                )
                continue

        return coordinates
