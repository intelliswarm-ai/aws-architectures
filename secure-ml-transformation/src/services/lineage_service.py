"""Service for data lineage tracking and management."""

import json
from datetime import datetime
from typing import Any
from uuid import uuid4

from aws_lambda_powertools import Logger

from src.common.clients import get_s3_client
from src.common.config import get_settings
from src.common.exceptions import LineageError
from src.common.models import JobExecutionStatus, LineageRecord

logger = Logger()


class LineageService:
    """Service for tracking data lineage."""

    def __init__(self) -> None:
        """Initialize lineage service."""
        self._settings = get_settings()
        self._s3_client = get_s3_client()
        self._lineage_prefix = "lineage"

    def record_lineage(self, lineage: LineageRecord) -> str:
        """Record a lineage entry.

        Args:
            lineage: Lineage record to store

        Returns:
            Lineage ID

        Raises:
            LineageError: If lineage recording fails
        """
        lineage_id = str(uuid4())

        try:
            # Store lineage in S3 for durability
            key = self._get_lineage_key(lineage.job_execution_id)

            self._s3_client.put_object(
                Bucket=self._settings.processed_data_bucket,
                Key=key,
                Body=json.dumps(lineage.model_dump(mode="json"), default=str),
                ContentType="application/json",
                ServerSideEncryption="aws:kms",
                SSEKMSKeyId=self._settings.kms_key_id,
                Metadata={
                    "lineage_id": lineage_id,
                    "job_name": lineage.job_name,
                    "status": lineage.status.value,
                },
            )

            logger.info(
                "Lineage recorded",
                extra={
                    "lineage_id": lineage_id,
                    "job_execution_id": lineage.job_execution_id,
                    "job_name": lineage.job_name,
                },
            )

            return lineage_id

        except Exception as e:
            logger.exception("Failed to record lineage")
            raise LineageError(
                message="Failed to record lineage",
                job_execution_id=lineage.job_execution_id,
                details={"error": str(e)},
            ) from e

    def get_lineage(self, job_execution_id: str) -> LineageRecord | None:
        """Get lineage for a specific job execution.

        Args:
            job_execution_id: Job execution ID

        Returns:
            Lineage record or None if not found
        """
        try:
            key = self._get_lineage_key(job_execution_id)

            response = self._s3_client.get_object(
                Bucket=self._settings.processed_data_bucket,
                Key=key,
            )

            data = json.loads(response["Body"].read().decode("utf-8"))

            # Convert datetime strings back to datetime objects
            if data.get("start_time"):
                data["start_time"] = datetime.fromisoformat(data["start_time"])
            if data.get("end_time"):
                data["end_time"] = datetime.fromisoformat(data["end_time"])

            return LineageRecord(**data)

        except self._s3_client.exceptions.NoSuchKey:
            logger.warning(
                "Lineage not found",
                extra={"job_execution_id": job_execution_id},
            )
            return None

        except Exception as e:
            logger.exception(
                "Failed to get lineage",
                extra={"job_execution_id": job_execution_id},
            )
            return None

    def update_status(
        self,
        job_execution_id: str,
        status: JobExecutionStatus,
        end_time: datetime | None = None,
        details: dict[str, Any] | None = None,
    ) -> bool:
        """Update lineage status.

        Args:
            job_execution_id: Job execution ID
            status: New status
            end_time: Job end time
            details: Additional details to add

        Returns:
            True if successful
        """
        lineage = self.get_lineage(job_execution_id)

        if not lineage:
            logger.warning(
                "Cannot update status - lineage not found",
                extra={"job_execution_id": job_execution_id},
            )
            return False

        # Update fields
        lineage.status = status
        if end_time:
            lineage.end_time = end_time
        if details:
            lineage.parameters.update(details)

        try:
            self.record_lineage(lineage)
            return True

        except LineageError:
            return False

    def get_lineage_history(
        self,
        path: str,
        limit: int = 100,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> list[LineageRecord]:
        """Get lineage history for a data path.

        Args:
            path: S3 path to query lineage for
            limit: Maximum records to return
            start_date: Filter by start date
            end_date: Filter by end date

        Returns:
            List of lineage records
        """
        try:
            # List all lineage objects
            paginator = self._s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=self._settings.processed_data_bucket,
                Prefix=f"{self._lineage_prefix}/",
                MaxKeys=1000,
            )

            records = []
            for page in pages:
                for obj in page.get("Contents", []):
                    if len(records) >= limit:
                        break

                    try:
                        response = self._s3_client.get_object(
                            Bucket=self._settings.processed_data_bucket,
                            Key=obj["Key"],
                        )
                        data = json.loads(response["Body"].read().decode("utf-8"))

                        # Check if path matches
                        input_paths = data.get("input_paths", [])
                        output_paths = data.get("output_paths", [])
                        if not any(path in p for p in input_paths + output_paths):
                            continue

                        # Parse datetime
                        if data.get("start_time"):
                            data["start_time"] = datetime.fromisoformat(data["start_time"])
                        if data.get("end_time"):
                            data["end_time"] = datetime.fromisoformat(data["end_time"])

                        lineage = LineageRecord(**data)

                        # Apply date filters
                        if start_date and lineage.start_time < start_date:
                            continue
                        if end_date and lineage.start_time > end_date:
                            continue

                        records.append(lineage)

                    except Exception as e:
                        logger.warning(
                            f"Failed to parse lineage record: {e}",
                            extra={"key": obj["Key"]},
                        )
                        continue

            # Sort by start time descending
            records.sort(key=lambda x: x.start_time, reverse=True)

            return records[:limit]

        except Exception as e:
            logger.exception("Failed to get lineage history")
            return []

    def get_downstream_lineage(
        self,
        job_execution_id: str,
        depth: int = 5,
    ) -> list[LineageRecord]:
        """Get downstream lineage (jobs that consumed this job's output).

        Args:
            job_execution_id: Starting job execution ID
            depth: Maximum depth to traverse

        Returns:
            List of downstream lineage records
        """
        lineage = self.get_lineage(job_execution_id)
        if not lineage:
            return []

        output_paths = lineage.output_paths
        downstream = []

        for path in output_paths:
            # Find jobs that used this path as input
            related = self.get_lineage_history(path, limit=100)
            for record in related:
                if record.job_execution_id != job_execution_id:
                    if any(path in p for p in record.input_paths):
                        downstream.append(record)

        return downstream

    def _get_lineage_key(self, job_execution_id: str) -> str:
        """Generate S3 key for lineage storage.

        Args:
            job_execution_id: Job execution ID

        Returns:
            S3 key
        """
        return f"{self._lineage_prefix}/{job_execution_id}.json"
