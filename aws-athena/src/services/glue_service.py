"""Glue service for ETL job and crawler management."""

import time
from typing import Any

import boto3

from ..common.config import settings
from ..common.exceptions import CrawlerError, ETLJobError
from ..common.models import (
    CrawlerRun,
    CrawlerStatus,
    ETLJob,
    ETLJobRun,
    JobStatus,
    S3Location,
    TableDefinition,
)


class GlueService:
    """Service for AWS Glue operations."""

    def __init__(self) -> None:
        """Initialize the Glue service."""
        self.client = boto3.client("glue", region_name=settings.aws_region)
        self.database = settings.glue_database

    def create_database(self, database: str | None = None) -> None:
        """Create a Glue database if it doesn't exist.

        Args:
            database: Database name (defaults to config)
        """
        db_name = database or self.database
        try:
            self.client.create_database(
                DatabaseInput={
                    "Name": db_name,
                    "Description": f"Data lake database for analytics",
                }
            )
        except self.client.exceptions.AlreadyExistsException:
            pass

    def create_table(self, table_def: TableDefinition) -> None:
        """Create a Glue table.

        Args:
            table_def: Table definition
        """
        columns = [
            {"Name": col.name, "Type": col.data_type, "Comment": col.comment or ""}
            for col in table_def.columns
            if not col.is_partition_key
        ]

        partition_keys = [
            {"Name": col.name, "Type": col.data_type, "Comment": col.comment or ""}
            for col in table_def.partition_keys
        ]

        serde_info = self._get_serde_info(table_def.data_format.value)
        input_format, output_format = self._get_io_formats(table_def.data_format.value)

        self.client.create_table(
            DatabaseName=table_def.database,
            TableInput={
                "Name": table_def.table_name,
                "Description": table_def.description or "",
                "StorageDescriptor": {
                    "Columns": columns,
                    "Location": table_def.location.uri,
                    "InputFormat": input_format,
                    "OutputFormat": output_format,
                    "SerdeInfo": serde_info,
                    "Compressed": table_def.compression.value != "none",
                },
                "PartitionKeys": partition_keys,
                "TableType": "EXTERNAL_TABLE",
                "Parameters": {
                    "classification": table_def.data_format.value,
                    "compressionType": table_def.compression.value,
                },
            },
        )

    def get_table(self, table_name: str, database: str | None = None) -> dict[str, Any]:
        """Get table metadata.

        Args:
            table_name: Table name
            database: Database name

        Returns:
            Table metadata
        """
        response = self.client.get_table(
            DatabaseName=database or self.database,
            Name=table_name,
        )
        return response["Table"]

    def add_partition(
        self,
        table_name: str,
        partition_values: list[str],
        location: str,
        database: str | None = None,
    ) -> None:
        """Add a partition to a table.

        Args:
            table_name: Table name
            partition_values: Partition column values
            location: S3 location for the partition
            database: Database name
        """
        table = self.get_table(table_name, database)
        storage_descriptor = table["StorageDescriptor"].copy()
        storage_descriptor["Location"] = location

        try:
            self.client.create_partition(
                DatabaseName=database or self.database,
                TableName=table_name,
                PartitionInput={
                    "Values": partition_values,
                    "StorageDescriptor": storage_descriptor,
                },
            )
        except self.client.exceptions.AlreadyExistsException:
            pass

    def start_etl_job(
        self,
        job_name: str | None = None,
        arguments: dict[str, str] | None = None,
    ) -> str:
        """Start a Glue ETL job.

        Args:
            job_name: Job name (defaults to config)
            arguments: Job arguments

        Returns:
            Job run ID
        """
        job = job_name or settings.glue_etl_job_name
        params: dict[str, Any] = {"JobName": job}

        if arguments:
            params["Arguments"] = arguments

        response = self.client.start_job_run(**params)
        return response["JobRunId"]

    def get_job_run(self, job_run_id: str, job_name: str | None = None) -> ETLJobRun:
        """Get ETL job run details.

        Args:
            job_run_id: Job run ID
            job_name: Job name

        Returns:
            ETL job run details
        """
        job = job_name or settings.glue_etl_job_name
        response = self.client.get_job_run(JobName=job, RunId=job_run_id)
        run = response["JobRun"]

        return ETLJobRun(
            job_name=job,
            job_run_id=job_run_id,
            status=JobStatus(run["JobRunState"]),
            started_on=run["StartedOn"],
            completed_on=run.get("CompletedOn"),
            execution_time_seconds=run.get("ExecutionTime"),
            error_message=run.get("ErrorMessage"),
            dpu_seconds=run.get("DPUSeconds"),
        )

    def wait_for_job_completion(
        self,
        job_run_id: str,
        job_name: str | None = None,
        timeout: int = 3600,
    ) -> ETLJobRun:
        """Wait for ETL job to complete.

        Args:
            job_run_id: Job run ID
            job_name: Job name
            timeout: Timeout in seconds

        Returns:
            Completed job run details

        Raises:
            ETLJobError: If job fails or times out
        """
        start_time = time.time()
        poll_interval = 10

        while True:
            job_run = self.get_job_run(job_run_id, job_name)

            if job_run.status == JobStatus.SUCCEEDED:
                return job_run

            if job_run.status in (JobStatus.FAILED, JobStatus.STOPPED, JobStatus.TIMEOUT):
                raise ETLJobError(
                    message=f"Job failed: {job_run.error_message}",
                    job_name=job_name or settings.glue_etl_job_name,
                    job_run_id=job_run_id,
                )

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.stop_job_run(job_run_id, job_name)
                raise ETLJobError(
                    message=f"Job timed out after {timeout} seconds",
                    job_name=job_name or settings.glue_etl_job_name,
                    job_run_id=job_run_id,
                )

            time.sleep(poll_interval)

    def stop_job_run(self, job_run_id: str, job_name: str | None = None) -> None:
        """Stop a running ETL job.

        Args:
            job_run_id: Job run ID
            job_name: Job name
        """
        self.client.batch_stop_job_run(
            JobName=job_name or settings.glue_etl_job_name,
            JobRunIds=[job_run_id],
        )

    def start_crawler(self, crawler_name: str | None = None) -> None:
        """Start a Glue crawler.

        Args:
            crawler_name: Crawler name (defaults to config)
        """
        crawler = crawler_name or settings.glue_crawler_name
        self.client.start_crawler(Name=crawler)

    def get_crawler_status(self, crawler_name: str | None = None) -> CrawlerRun:
        """Get crawler status.

        Args:
            crawler_name: Crawler name

        Returns:
            Crawler run details
        """
        crawler = crawler_name or settings.glue_crawler_name
        response = self.client.get_crawler(Name=crawler)
        crawler_info = response["Crawler"]

        last_crawl = crawler_info.get("LastCrawl", {})

        return CrawlerRun(
            crawler_name=crawler,
            status=CrawlerStatus(crawler_info["State"]),
            last_crawl_time=last_crawl.get("StartTime"),
            tables_created=last_crawl.get("TablesCreated", 0),
            tables_updated=last_crawl.get("TablesUpdated", 0),
            tables_deleted=last_crawl.get("TablesDeleted", 0),
        )

    def wait_for_crawler_completion(
        self,
        crawler_name: str | None = None,
        timeout: int = 1800,
    ) -> CrawlerRun:
        """Wait for crawler to complete.

        Args:
            crawler_name: Crawler name
            timeout: Timeout in seconds

        Returns:
            Completed crawler run details

        Raises:
            CrawlerError: If crawler fails or times out
        """
        crawler = crawler_name or settings.glue_crawler_name
        start_time = time.time()
        poll_interval = 30

        while True:
            crawler_run = self.get_crawler_status(crawler)

            if crawler_run.status == CrawlerStatus.READY:
                return crawler_run

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.stop_crawler(crawler)
                raise CrawlerError(
                    message=f"Crawler timed out after {timeout} seconds",
                    crawler_name=crawler,
                )

            time.sleep(poll_interval)

    def stop_crawler(self, crawler_name: str | None = None) -> None:
        """Stop a running crawler.

        Args:
            crawler_name: Crawler name
        """
        self.client.stop_crawler(Name=crawler_name or settings.glue_crawler_name)

    def create_etl_job(self, job: ETLJob) -> None:
        """Create a Glue ETL job.

        Args:
            job: ETL job definition
        """
        self.client.create_job(
            Name=job.job_name,
            Description=job.description or "",
            Role=job.role_arn,
            Command={
                "Name": "glueetl",
                "ScriptLocation": job.script_location,
                "PythonVersion": "3",
            },
            DefaultArguments={
                "--job-language": "python",
                "--enable-metrics": "true",
                "--enable-continuous-cloudwatch-log": "true",
                "--source_location": job.source_location.uri,
                "--target_location": job.target_location.uri,
                "--source_format": job.source_format.value,
                "--target_format": job.target_format.value,
                "--compression": job.compression.value,
            },
            MaxCapacity=job.max_capacity,
            Timeout=job.timeout_minutes,
            GlueVersion="4.0",
        )

    def _get_serde_info(self, data_format: str) -> dict[str, Any]:
        """Get SerDe info for a data format."""
        serde_map = {
            "parquet": {
                "SerializationLibrary": "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe",
            },
            "json": {
                "SerializationLibrary": "org.openx.data.jsonserde.JsonSerDe",
            },
            "orc": {
                "SerializationLibrary": "org.apache.hadoop.hive.ql.io.orc.OrcSerde",
            },
            "csv": {
                "SerializationLibrary": "org.apache.hadoop.hive.serde2.lazy.LazySimpleSerDe",
                "Parameters": {"field.delim": ","},
            },
        }
        return serde_map.get(data_format, serde_map["json"])

    def _get_io_formats(self, data_format: str) -> tuple[str, str]:
        """Get input/output formats for a data format."""
        format_map = {
            "parquet": (
                "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat",
                "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat",
            ),
            "json": (
                "org.apache.hadoop.mapred.TextInputFormat",
                "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
            ),
            "orc": (
                "org.apache.hadoop.hive.ql.io.orc.OrcInputFormat",
                "org.apache.hadoop.hive.ql.io.orc.OrcOutputFormat",
            ),
            "csv": (
                "org.apache.hadoop.mapred.TextInputFormat",
                "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat",
            ),
        }
        return format_map.get(data_format, format_map["json"])
