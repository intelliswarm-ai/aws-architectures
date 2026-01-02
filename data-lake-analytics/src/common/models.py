"""Pydantic data models for AWS Athena data lake analytics."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class DataFormat(str, Enum):
    """Supported data formats."""

    JSON = "json"
    PARQUET = "parquet"
    ORC = "orc"
    CSV = "csv"
    AVRO = "avro"


class CompressionType(str, Enum):
    """Compression types."""

    NONE = "none"
    SNAPPY = "snappy"
    GZIP = "gzip"
    LZO = "lzo"
    ZLIB = "zlib"


class QueryState(str, Enum):
    """Athena query execution states."""

    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class JobStatus(str, Enum):
    """Glue ETL job status."""

    STARTING = "STARTING"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"
    STOPPED = "STOPPED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    TIMEOUT = "TIMEOUT"


class CrawlerStatus(str, Enum):
    """Glue crawler status."""

    READY = "READY"
    RUNNING = "RUNNING"
    STOPPING = "STOPPING"


class PermissionType(str, Enum):
    """Lake Formation permission types."""

    SELECT = "SELECT"
    INSERT = "INSERT"
    DELETE = "DELETE"
    DESCRIBE = "DESCRIBE"
    ALTER = "ALTER"
    DROP = "DROP"
    CREATE_TABLE = "CREATE_TABLE"
    DATA_LOCATION_ACCESS = "DATA_LOCATION_ACCESS"


class S3Location(BaseModel):
    """S3 location specification."""

    bucket: str
    prefix: str
    region: str | None = None

    @property
    def uri(self) -> str:
        """Get S3 URI."""
        return f"s3://{self.bucket}/{self.prefix}"


class PartitionSpec(BaseModel):
    """Partition specification for time-based partitioning."""

    year: str
    month: str
    day: str
    hour: str | None = None

    @property
    def path(self) -> str:
        """Get partition path."""
        parts = [f"year={self.year}", f"month={self.month}", f"day={self.day}"]
        if self.hour:
            parts.append(f"hour={self.hour}")
        return "/".join(parts)

    @classmethod
    def from_datetime(cls, dt: datetime, include_hour: bool = True) -> "PartitionSpec":
        """Create partition spec from datetime."""
        return cls(
            year=str(dt.year),
            month=f"{dt.month:02d}",
            day=f"{dt.day:02d}",
            hour=f"{dt.hour:02d}" if include_hour else None,
        )


class ColumnDefinition(BaseModel):
    """Column definition for table schema."""

    name: str
    data_type: str
    comment: str | None = None
    is_partition_key: bool = False


class TableDefinition(BaseModel):
    """Table definition for Glue catalog."""

    database: str
    table_name: str
    columns: list[ColumnDefinition]
    partition_keys: list[ColumnDefinition] = []
    location: S3Location
    data_format: DataFormat = DataFormat.PARQUET
    compression: CompressionType = CompressionType.SNAPPY
    description: str | None = None


class AthenaQuery(BaseModel):
    """Athena query specification."""

    query: str
    database: str
    workgroup: str = "primary"
    output_location: str | None = None
    client_request_token: str | None = None


class QueryExecution(BaseModel):
    """Athena query execution details."""

    query_execution_id: str
    query: str
    database: str
    state: QueryState
    state_change_reason: str | None = None
    submission_time: datetime
    completion_time: datetime | None = None
    data_scanned_bytes: int | None = None
    execution_time_ms: int | None = None
    output_location: str | None = None


class AthenaQueryResult(BaseModel):
    """Athena query result."""

    query_execution_id: str
    columns: list[str]
    rows: list[dict[str, Any]]
    next_token: str | None = None
    total_rows: int = 0


class ETLJob(BaseModel):
    """Glue ETL job definition."""

    job_name: str
    description: str | None = None
    role_arn: str
    script_location: str
    source_location: S3Location
    target_location: S3Location
    source_format: DataFormat = DataFormat.JSON
    target_format: DataFormat = DataFormat.PARQUET
    compression: CompressionType = CompressionType.SNAPPY
    max_capacity: float = 2.0
    timeout_minutes: int = 60


class ETLJobRun(BaseModel):
    """Glue ETL job run details."""

    job_name: str
    job_run_id: str
    status: JobStatus
    started_on: datetime
    completed_on: datetime | None = None
    execution_time_seconds: int | None = None
    error_message: str | None = None
    dpu_seconds: float | None = None


class CrawlerRun(BaseModel):
    """Glue crawler run details."""

    crawler_name: str
    status: CrawlerStatus
    last_crawl_time: datetime | None = None
    tables_created: int = 0
    tables_updated: int = 0
    tables_deleted: int = 0


class LakeFormationPermission(BaseModel):
    """Lake Formation permission grant."""

    principal: str
    resource_type: str  # DATABASE, TABLE, COLUMN, DATA_LOCATION
    resource_arn: str
    permissions: list[PermissionType]
    permissions_with_grant_option: list[PermissionType] = []


class EventDocument(BaseModel):
    """Sample event document for ingestion."""

    event_id: str
    timestamp: datetime
    event_type: str
    user_id: str
    session_id: str | None = None
    properties: dict[str, Any] = {}
    geo: dict[str, Any] = {}


class IngestionResult(BaseModel):
    """Result of data ingestion."""

    s3_key: str
    bucket: str
    records_written: int
    bytes_written: int
    partition: PartitionSpec
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class QueryMetrics(BaseModel):
    """Query performance metrics."""

    query_execution_id: str
    data_scanned_bytes: int
    execution_time_ms: int
    query_queue_time_ms: int | None = None
    query_planning_time_ms: int | None = None
    service_processing_time_ms: int | None = None
    estimated_cost_usd: float | None = None

    @property
    def data_scanned_gb(self) -> float:
        """Get data scanned in GB."""
        return self.data_scanned_bytes / (1024**3)

    def calculate_cost(self, price_per_tb: float = 5.0) -> float:
        """Calculate query cost based on data scanned."""
        tb_scanned = self.data_scanned_bytes / (1024**4)
        return tb_scanned * price_per_tb
