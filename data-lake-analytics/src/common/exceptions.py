"""Custom exceptions for AWS Athena data lake analytics."""


class DataLakeError(Exception):
    """Base exception for data lake errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class AthenaError(DataLakeError):
    """Raised when Athena operations fail."""

    def __init__(self, message: str, query_execution_id: str | None = None) -> None:
        self.query_execution_id = query_execution_id
        super().__init__(message, error_code="ATHENA_ERROR")


class QueryExecutionError(AthenaError):
    """Raised when a query execution fails."""

    def __init__(
        self,
        message: str,
        query_execution_id: str,
        state_change_reason: str | None = None,
    ) -> None:
        self.state_change_reason = state_change_reason
        super().__init__(message, query_execution_id=query_execution_id)
        self.error_code = "QUERY_EXECUTION_ERROR"


class QueryTimeoutError(AthenaError):
    """Raised when a query times out."""

    def __init__(self, query_execution_id: str, timeout_seconds: int) -> None:
        self.timeout_seconds = timeout_seconds
        message = f"Query {query_execution_id} timed out after {timeout_seconds} seconds"
        super().__init__(message, query_execution_id=query_execution_id)
        self.error_code = "QUERY_TIMEOUT"


class ETLJobError(DataLakeError):
    """Raised when Glue ETL job operations fail."""

    def __init__(
        self,
        message: str,
        job_name: str | None = None,
        job_run_id: str | None = None,
    ) -> None:
        self.job_name = job_name
        self.job_run_id = job_run_id
        super().__init__(message, error_code="ETL_JOB_ERROR")


class CrawlerError(DataLakeError):
    """Raised when Glue crawler operations fail."""

    def __init__(self, message: str, crawler_name: str | None = None) -> None:
        self.crawler_name = crawler_name
        super().__init__(message, error_code="CRAWLER_ERROR")


class LakeFormationError(DataLakeError):
    """Raised when Lake Formation operations fail."""

    def __init__(
        self,
        message: str,
        principal: str | None = None,
        resource: str | None = None,
    ) -> None:
        self.principal = principal
        self.resource = resource
        super().__init__(message, error_code="LAKEFORMATION_ERROR")


class PermissionDeniedError(LakeFormationError):
    """Raised when Lake Formation permission is denied."""

    def __init__(self, principal: str, resource: str, action: str) -> None:
        self.action = action
        message = f"Permission denied: {principal} cannot perform {action} on {resource}"
        super().__init__(message, principal=principal, resource=resource)
        self.error_code = "PERMISSION_DENIED"


class DataLocationError(LakeFormationError):
    """Raised when data location access fails."""

    def __init__(self, location: str, reason: str) -> None:
        self.location = location
        message = f"Data location error for {location}: {reason}"
        super().__init__(message)
        self.error_code = "DATA_LOCATION_ERROR"


class SchemaError(DataLakeError):
    """Raised when schema operations fail."""

    def __init__(self, message: str, table_name: str | None = None) -> None:
        self.table_name = table_name
        super().__init__(message, error_code="SCHEMA_ERROR")


class PartitionError(DataLakeError):
    """Raised when partition operations fail."""

    def __init__(self, message: str, partition_spec: str | None = None) -> None:
        self.partition_spec = partition_spec
        super().__init__(message, error_code="PARTITION_ERROR")
