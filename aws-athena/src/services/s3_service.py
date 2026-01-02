"""S3 service for data ingestion and storage operations."""

import json
from datetime import datetime
from io import BytesIO
from typing import Any

import boto3
from botocore.exceptions import ClientError

from ..common.config import settings
from ..common.models import (
    EventDocument,
    IngestionResult,
    PartitionSpec,
    S3Location,
)


class S3Service:
    """Service for S3 data operations."""

    def __init__(self) -> None:
        """Initialize the S3 service."""
        self.client = boto3.client("s3", region_name=settings.aws_region)
        self.raw_bucket = settings.raw_bucket
        self.processed_bucket = settings.processed_bucket
        self.results_bucket = settings.results_bucket

    def write_json_documents(
        self,
        documents: list[EventDocument],
        partition: PartitionSpec | None = None,
        bucket: str | None = None,
    ) -> IngestionResult:
        """Write JSON documents to S3 with partitioning.

        Documents are written as newline-delimited JSON (NDJSON)
        which is optimal for Athena and Glue processing.

        Args:
            documents: List of event documents to write
            partition: Partition specification (defaults to current time)
            bucket: Target bucket (defaults to raw bucket)

        Returns:
            Ingestion result with S3 location and stats
        """
        target_bucket = bucket or self.raw_bucket
        part = partition or PartitionSpec.from_datetime(datetime.utcnow())

        # Create NDJSON content
        content_lines = [doc.model_dump_json() for doc in documents]
        content = "\n".join(content_lines)
        content_bytes = content.encode("utf-8")

        # Generate unique key with partition path
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        s3_key = f"raw/{part.path}/events_{timestamp}.json"

        self.client.put_object(
            Bucket=target_bucket,
            Key=s3_key,
            Body=content_bytes,
            ContentType="application/json",
        )

        return IngestionResult(
            s3_key=s3_key,
            bucket=target_bucket,
            records_written=len(documents),
            bytes_written=len(content_bytes),
            partition=part,
        )

    def write_json_batch(
        self,
        records: list[dict[str, Any]],
        prefix: str,
        partition: PartitionSpec | None = None,
        bucket: str | None = None,
    ) -> str:
        """Write raw JSON records as NDJSON.

        Args:
            records: List of dictionaries to write
            prefix: S3 key prefix
            partition: Optional partition spec
            bucket: Target bucket

        Returns:
            S3 key where data was written
        """
        target_bucket = bucket or self.raw_bucket
        part = partition or PartitionSpec.from_datetime(datetime.utcnow())

        content_lines = [json.dumps(record) for record in records]
        content = "\n".join(content_lines)

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
        s3_key = f"{prefix}/{part.path}/batch_{timestamp}.json"

        self.client.put_object(
            Bucket=target_bucket,
            Key=s3_key,
            Body=content.encode("utf-8"),
            ContentType="application/json",
        )

        return s3_key

    def list_objects(
        self,
        prefix: str,
        bucket: str | None = None,
        max_keys: int = 1000,
    ) -> list[dict[str, Any]]:
        """List objects in S3 with prefix.

        Args:
            prefix: S3 key prefix
            bucket: Bucket name
            max_keys: Maximum objects to return

        Returns:
            List of object metadata
        """
        target_bucket = bucket or self.raw_bucket
        objects = []

        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(
            Bucket=target_bucket, Prefix=prefix, PaginationConfig={"MaxItems": max_keys}
        ):
            for obj in page.get("Contents", []):
                objects.append(
                    {
                        "key": obj["Key"],
                        "size": obj["Size"],
                        "last_modified": obj["LastModified"],
                        "storage_class": obj.get("StorageClass", "STANDARD"),
                    }
                )

        return objects

    def get_object_content(
        self,
        key: str,
        bucket: str | None = None,
    ) -> bytes:
        """Get object content.

        Args:
            key: S3 key
            bucket: Bucket name

        Returns:
            Object content as bytes
        """
        response = self.client.get_object(
            Bucket=bucket or self.raw_bucket,
            Key=key,
        )
        return response["Body"].read()

    def read_json_lines(
        self,
        key: str,
        bucket: str | None = None,
    ) -> list[dict[str, Any]]:
        """Read NDJSON file and parse each line.

        Args:
            key: S3 key
            bucket: Bucket name

        Returns:
            List of parsed JSON objects
        """
        content = self.get_object_content(key, bucket)
        lines = content.decode("utf-8").strip().split("\n")
        return [json.loads(line) for line in lines if line]

    def delete_objects(
        self,
        keys: list[str],
        bucket: str | None = None,
    ) -> int:
        """Delete multiple objects.

        Args:
            keys: List of S3 keys to delete
            bucket: Bucket name

        Returns:
            Number of objects deleted
        """
        if not keys:
            return 0

        target_bucket = bucket or self.raw_bucket

        # Delete in batches of 1000 (S3 limit)
        deleted = 0
        for i in range(0, len(keys), 1000):
            batch = keys[i : i + 1000]
            objects = [{"Key": key} for key in batch]

            response = self.client.delete_objects(
                Bucket=target_bucket,
                Delete={"Objects": objects, "Quiet": True},
            )
            deleted += len(batch) - len(response.get("Errors", []))

        return deleted

    def copy_object(
        self,
        source_key: str,
        dest_key: str,
        source_bucket: str | None = None,
        dest_bucket: str | None = None,
    ) -> None:
        """Copy an object within or between buckets.

        Args:
            source_key: Source S3 key
            dest_key: Destination S3 key
            source_bucket: Source bucket
            dest_bucket: Destination bucket
        """
        src_bucket = source_bucket or self.raw_bucket
        dst_bucket = dest_bucket or self.processed_bucket

        self.client.copy_object(
            CopySource={"Bucket": src_bucket, "Key": source_key},
            Bucket=dst_bucket,
            Key=dest_key,
        )

    def get_bucket_location(self, bucket: str) -> S3Location:
        """Get S3 bucket location details.

        Args:
            bucket: Bucket name

        Returns:
            S3Location with bucket info
        """
        response = self.client.get_bucket_location(Bucket=bucket)
        region = response.get("LocationConstraint") or "us-east-1"

        return S3Location(
            bucket=bucket,
            prefix="",
            region=region,
        )

    def check_bucket_exists(self, bucket: str) -> bool:
        """Check if bucket exists and is accessible.

        Args:
            bucket: Bucket name

        Returns:
            True if bucket exists and is accessible
        """
        try:
            self.client.head_bucket(Bucket=bucket)
            return True
        except ClientError:
            return False

    def get_partition_sizes(
        self,
        prefix: str,
        bucket: str | None = None,
    ) -> dict[str, int]:
        """Get size of each partition under a prefix.

        Useful for monitoring data distribution across partitions.

        Args:
            prefix: S3 key prefix (e.g., "raw/")
            bucket: Bucket name

        Returns:
            Dictionary mapping partition paths to total size in bytes
        """
        target_bucket = bucket or self.raw_bucket
        partition_sizes: dict[str, int] = {}

        paginator = self.client.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=target_bucket, Prefix=prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                size = obj["Size"]

                # Extract partition path (year=.../month=.../day=...)
                parts = key.replace(prefix, "").split("/")
                partition_parts = [p for p in parts if "=" in p]
                if partition_parts:
                    partition_path = "/".join(partition_parts)
                    partition_sizes[partition_path] = (
                        partition_sizes.get(partition_path, 0) + size
                    )

        return partition_sizes

    def generate_presigned_url(
        self,
        key: str,
        bucket: str | None = None,
        expiration: int = 3600,
        method: str = "get_object",
    ) -> str:
        """Generate a presigned URL for object access.

        Args:
            key: S3 key
            bucket: Bucket name
            expiration: URL expiration in seconds
            method: S3 method (get_object, put_object)

        Returns:
            Presigned URL
        """
        return self.client.generate_presigned_url(
            ClientMethod=method,
            Params={
                "Bucket": bucket or self.results_bucket,
                "Key": key,
            },
            ExpiresIn=expiration,
        )

    def get_object_metadata(
        self,
        key: str,
        bucket: str | None = None,
    ) -> dict[str, Any]:
        """Get object metadata without downloading content.

        Args:
            key: S3 key
            bucket: Bucket name

        Returns:
            Object metadata
        """
        response = self.client.head_object(
            Bucket=bucket or self.raw_bucket,
            Key=key,
        )

        return {
            "content_length": response["ContentLength"],
            "content_type": response.get("ContentType"),
            "last_modified": response["LastModified"],
            "etag": response["ETag"],
            "metadata": response.get("Metadata", {}),
        }
