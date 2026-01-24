"""Service for AWS Glue operations."""

from typing import Any

from aws_lambda_powertools import Logger

from src.common.clients import get_glue_client
from src.common.config import get_settings
from src.common.exceptions import GlueJobError

logger = Logger()


class GlueService:
    """Service for interacting with AWS Glue."""

    def __init__(self) -> None:
        """Initialize Glue service."""
        self._client = get_glue_client()
        self._settings = get_settings()

    def start_job(
        self,
        job_name: str,
        arguments: dict[str, str] | None = None,
        worker_type: str = "G.1X",
        number_of_workers: int = 10,
    ) -> str:
        """Start a Glue ETL job.

        Args:
            job_name: Name of the Glue job to start
            arguments: Job arguments as key-value pairs
            worker_type: Worker type (Standard, G.1X, G.2X)
            number_of_workers: Number of workers to allocate

        Returns:
            Job run ID

        Raises:
            GlueJobError: If job fails to start
        """
        try:
            response = self._client.start_job_run(
                JobName=job_name,
                Arguments=arguments or {},
                WorkerType=worker_type,
                NumberOfWorkers=number_of_workers,
            )

            job_run_id = response["JobRunId"]
            logger.info(
                "Glue job started",
                extra={
                    "job_name": job_name,
                    "job_run_id": job_run_id,
                    "worker_type": worker_type,
                    "number_of_workers": number_of_workers,
                },
            )

            return job_run_id

        except Exception as e:
            logger.exception("Failed to start Glue job", extra={"job_name": job_name})
            raise GlueJobError(
                message=f"Failed to start Glue job: {job_name}",
                job_name=job_name,
                error_message=str(e),
            ) from e

    def get_job_run(self, job_name: str, run_id: str) -> dict[str, Any]:
        """Get details of a specific job run.

        Args:
            job_name: Name of the Glue job
            run_id: Job run ID

        Returns:
            Job run details

        Raises:
            GlueJobError: If job run not found
        """
        try:
            response = self._client.get_job_run(
                JobName=job_name,
                RunId=run_id,
            )
            return response["JobRun"]

        except self._client.exceptions.EntityNotFoundException as e:
            raise GlueJobError(
                message=f"Job run not found: {run_id}",
                job_name=job_name,
                job_run_id=run_id,
            ) from e

        except Exception as e:
            logger.exception(
                "Failed to get job run",
                extra={"job_name": job_name, "run_id": run_id},
            )
            raise GlueJobError(
                message="Failed to get job run",
                job_name=job_name,
                job_run_id=run_id,
                error_message=str(e),
            ) from e

    def get_job_runs(
        self,
        job_name: str,
        max_results: int = 10,
    ) -> list[dict[str, Any]]:
        """Get recent job runs for a job.

        Args:
            job_name: Name of the Glue job
            max_results: Maximum number of runs to return

        Returns:
            List of job run details
        """
        try:
            response = self._client.get_job_runs(
                JobName=job_name,
                MaxResults=max_results,
            )
            return response.get("JobRuns", [])

        except Exception as e:
            logger.exception("Failed to get job runs", extra={"job_name": job_name})
            raise GlueJobError(
                message="Failed to get job runs",
                job_name=job_name,
                error_message=str(e),
            ) from e

    def get_job_bookmark(self, job_name: str) -> dict[str, Any]:
        """Get job bookmark state for lineage tracking.

        Args:
            job_name: Name of the Glue job

        Returns:
            Job bookmark state
        """
        try:
            response = self._client.get_job_bookmark(JobName=job_name)
            return response.get("JobBookmarkEntry", {})

        except Exception as e:
            logger.warning(
                "Failed to get job bookmark",
                extra={"job_name": job_name, "error": str(e)},
            )
            return {}

    def reset_job_bookmark(self, job_name: str) -> bool:
        """Reset job bookmark to reprocess all data.

        Args:
            job_name: Name of the Glue job

        Returns:
            True if successful
        """
        try:
            self._client.reset_job_bookmark(JobName=job_name)
            logger.info("Job bookmark reset", extra={"job_name": job_name})
            return True

        except Exception as e:
            logger.exception(
                "Failed to reset job bookmark",
                extra={"job_name": job_name},
            )
            raise GlueJobError(
                message="Failed to reset job bookmark",
                job_name=job_name,
                error_message=str(e),
            ) from e

    def stop_job_run(self, job_name: str, run_id: str) -> bool:
        """Stop a running job.

        Args:
            job_name: Name of the Glue job
            run_id: Job run ID to stop

        Returns:
            True if successful
        """
        try:
            self._client.batch_stop_job_run(
                JobName=job_name,
                JobRunIds=[run_id],
            )
            logger.info(
                "Job run stopped",
                extra={"job_name": job_name, "run_id": run_id},
            )
            return True

        except Exception as e:
            logger.exception(
                "Failed to stop job run",
                extra={"job_name": job_name, "run_id": run_id},
            )
            raise GlueJobError(
                message="Failed to stop job run",
                job_name=job_name,
                job_run_id=run_id,
                error_message=str(e),
            ) from e

    def update_table_metadata(
        self,
        database_name: str,
        table_name: str,
        metadata: dict[str, str],
    ) -> bool:
        """Update Glue catalog table metadata for lineage.

        Args:
            database_name: Glue database name
            table_name: Table name
            metadata: Metadata key-value pairs

        Returns:
            True if successful
        """
        try:
            # Get current table definition
            response = self._client.get_table(
                DatabaseName=database_name,
                Name=table_name,
            )
            table = response["Table"]

            # Update parameters with new metadata
            current_params = table.get("Parameters", {})
            current_params.update(metadata)

            # Update table
            table_input = {
                "Name": table["Name"],
                "StorageDescriptor": table["StorageDescriptor"],
                "Parameters": current_params,
            }

            if "PartitionKeys" in table:
                table_input["PartitionKeys"] = table["PartitionKeys"]

            self._client.update_table(
                DatabaseName=database_name,
                TableInput=table_input,
            )

            logger.info(
                "Table metadata updated",
                extra={
                    "database": database_name,
                    "table": table_name,
                    "metadata_keys": list(metadata.keys()),
                },
            )
            return True

        except Exception as e:
            logger.exception(
                "Failed to update table metadata",
                extra={"database": database_name, "table": table_name},
            )
            return False
