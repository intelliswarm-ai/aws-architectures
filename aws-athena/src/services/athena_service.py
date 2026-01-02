"""Athena service for query execution and management."""

import time
from typing import Any

import boto3

from ..common.config import settings
from ..common.exceptions import QueryExecutionError, QueryTimeoutError
from ..common.models import (
    AthenaQuery,
    AthenaQueryResult,
    QueryExecution,
    QueryMetrics,
    QueryState,
)


class AthenaService:
    """Service for Athena query operations."""

    def __init__(self) -> None:
        """Initialize the Athena service."""
        self.client = boto3.client("athena", region_name=settings.aws_region)
        self.default_database = settings.glue_database
        self.default_workgroup = settings.athena_workgroup
        self.results_bucket = settings.results_bucket

    def execute_query(
        self,
        query: str,
        database: str | None = None,
        workgroup: str | None = None,
        wait: bool = True,
        timeout: int | None = None,
    ) -> QueryExecution:
        """Execute an Athena query.

        Args:
            query: SQL query string
            database: Database name (defaults to config)
            workgroup: Workgroup name (defaults to config)
            wait: Whether to wait for completion
            timeout: Query timeout in seconds

        Returns:
            QueryExecution with results

        Raises:
            QueryExecutionError: If query fails
            QueryTimeoutError: If query times out
        """
        athena_query = AthenaQuery(
            query=query,
            database=database or self.default_database,
            workgroup=workgroup or self.default_workgroup,
            output_location=f"s3://{self.results_bucket}/athena-results/",
        )

        response = self.client.start_query_execution(
            QueryString=athena_query.query,
            QueryExecutionContext={"Database": athena_query.database},
            WorkGroup=athena_query.workgroup,
            ResultConfiguration={"OutputLocation": athena_query.output_location},
        )

        query_execution_id = response["QueryExecutionId"]

        if wait:
            return self._wait_for_completion(
                query_execution_id, timeout or settings.athena_query_timeout
            )

        return self.get_query_execution(query_execution_id)

    def get_query_execution(self, query_execution_id: str) -> QueryExecution:
        """Get query execution details.

        Args:
            query_execution_id: The query execution ID

        Returns:
            QueryExecution details
        """
        response = self.client.get_query_execution(QueryExecutionId=query_execution_id)
        execution = response["QueryExecution"]
        status = execution["Status"]
        statistics = execution.get("Statistics", {})

        return QueryExecution(
            query_execution_id=query_execution_id,
            query=execution["Query"],
            database=execution.get("QueryExecutionContext", {}).get("Database", ""),
            state=QueryState(status["State"]),
            state_change_reason=status.get("StateChangeReason"),
            submission_time=status["SubmissionDateTime"],
            completion_time=status.get("CompletionDateTime"),
            data_scanned_bytes=statistics.get("DataScannedInBytes"),
            execution_time_ms=statistics.get("EngineExecutionTimeInMillis"),
            output_location=execution.get("ResultConfiguration", {}).get("OutputLocation"),
        )

    def get_query_results(
        self,
        query_execution_id: str,
        max_results: int = 1000,
        next_token: str | None = None,
    ) -> AthenaQueryResult:
        """Get query results.

        Args:
            query_execution_id: The query execution ID
            max_results: Maximum results to return
            next_token: Pagination token

        Returns:
            Query results with rows and columns
        """
        params: dict[str, Any] = {
            "QueryExecutionId": query_execution_id,
            "MaxResults": max_results,
        }
        if next_token:
            params["NextToken"] = next_token

        response = self.client.get_query_results(**params)
        result_set = response["ResultSet"]

        columns = [col["Name"] for col in result_set["ResultSetMetadata"]["ColumnInfo"]]

        rows = []
        for i, row in enumerate(result_set["Rows"]):
            if i == 0 and not next_token:
                continue
            row_data = {}
            for j, cell in enumerate(row["Data"]):
                row_data[columns[j]] = cell.get("VarCharValue")
            rows.append(row_data)

        return AthenaQueryResult(
            query_execution_id=query_execution_id,
            columns=columns,
            rows=rows,
            next_token=response.get("NextToken"),
            total_rows=len(rows),
        )

    def get_query_metrics(self, query_execution_id: str) -> QueryMetrics:
        """Get query performance metrics.

        Args:
            query_execution_id: The query execution ID

        Returns:
            Query metrics including cost estimation
        """
        execution = self.get_query_execution(query_execution_id)

        metrics = QueryMetrics(
            query_execution_id=query_execution_id,
            data_scanned_bytes=execution.data_scanned_bytes or 0,
            execution_time_ms=execution.execution_time_ms or 0,
        )
        metrics.estimated_cost_usd = metrics.calculate_cost()

        return metrics

    def cancel_query(self, query_execution_id: str) -> None:
        """Cancel a running query.

        Args:
            query_execution_id: The query execution ID
        """
        self.client.stop_query_execution(QueryExecutionId=query_execution_id)

    def list_query_executions(
        self,
        workgroup: str | None = None,
        max_results: int = 50,
    ) -> list[str]:
        """List recent query executions.

        Args:
            workgroup: Workgroup to filter by
            max_results: Maximum results

        Returns:
            List of query execution IDs
        """
        params: dict[str, Any] = {"MaxResults": max_results}
        if workgroup:
            params["WorkGroup"] = workgroup

        response = self.client.list_query_executions(**params)
        return response.get("QueryExecutionIds", [])

    def _wait_for_completion(
        self, query_execution_id: str, timeout: int
    ) -> QueryExecution:
        """Wait for query to complete.

        Args:
            query_execution_id: The query execution ID
            timeout: Timeout in seconds

        Returns:
            Completed QueryExecution

        Raises:
            QueryExecutionError: If query fails
            QueryTimeoutError: If query times out
        """
        start_time = time.time()
        poll_interval = 1

        while True:
            execution = self.get_query_execution(query_execution_id)

            if execution.state == QueryState.SUCCEEDED:
                return execution

            if execution.state == QueryState.FAILED:
                raise QueryExecutionError(
                    message=f"Query failed: {execution.state_change_reason}",
                    query_execution_id=query_execution_id,
                    state_change_reason=execution.state_change_reason,
                )

            if execution.state == QueryState.CANCELLED:
                raise QueryExecutionError(
                    message="Query was cancelled",
                    query_execution_id=query_execution_id,
                )

            elapsed = time.time() - start_time
            if elapsed >= timeout:
                self.cancel_query(query_execution_id)
                raise QueryTimeoutError(query_execution_id, timeout)

            time.sleep(poll_interval)
            poll_interval = min(poll_interval * 1.5, 10)
