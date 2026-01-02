"""Lambda handler for Athena query execution.

This handler provides an interface for executing Athena queries
against the data lake with support for parameterized queries,
result pagination, and query metrics.
"""

import json
import logging
from typing import Any

from ..common.config import settings
from ..common.exceptions import QueryExecutionError, QueryTimeoutError
from ..common.models import QueryState
from ..services import get_athena_service

logger = logging.getLogger()
logger.setLevel(settings.log_level)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle Athena query requests.

    Supports:
    - Direct query execution
    - Named/saved query execution
    - Query status polling
    - Result retrieval with pagination
    - Query cancellation

    Args:
        event: Lambda event
        context: Lambda context

    Returns:
        Query execution result
    """
    logger.info(f"Query handler invoked")

    try:
        event_type = _get_event_type(event)

        if event_type == "api_gateway":
            return _handle_api_request(event)
        else:
            return _handle_direct_invocation(event)

    except QueryExecutionError as e:
        logger.error(f"Query execution failed: {e}")
        return _error_response(400, str(e), e.query_execution_id)
    except QueryTimeoutError as e:
        logger.error(f"Query timed out: {e}")
        return _error_response(408, str(e), e.query_execution_id)
    except Exception as e:
        logger.exception(f"Query handler error: {e}")
        return _error_response(500, str(e))


def _get_event_type(event: dict[str, Any]) -> str:
    """Determine event source type."""
    if "httpMethod" in event or "requestContext" in event:
        return "api_gateway"
    return "direct"


def _handle_api_request(event: dict[str, Any]) -> dict[str, Any]:
    """Handle API Gateway request for query operations."""
    athena_service = get_athena_service()

    http_method = event.get("httpMethod", "POST")
    path = event.get("path", "/")

    # Parse request body
    body = event.get("body", "{}")
    if event.get("isBase64Encoded"):
        import base64

        body = base64.b64decode(body).decode("utf-8")

    data = json.loads(body) if body else {}

    # Handle different actions based on path/method
    if "/execute" in path or (http_method == "POST" and "query" in data):
        return _execute_query_api(data, athena_service)

    elif "/status" in path or data.get("action") == "status":
        return _get_query_status_api(data, event, athena_service)

    elif "/results" in path or data.get("action") == "results":
        return _get_query_results_api(data, event, athena_service)

    elif "/cancel" in path or data.get("action") == "cancel":
        return _cancel_query_api(data, event, athena_service)

    elif "/metrics" in path or data.get("action") == "metrics":
        return _get_query_metrics_api(data, event, athena_service)

    else:
        return _api_response(400, {"error": "Unknown action or endpoint"})


def _execute_query_api(data: dict[str, Any], athena_service: Any) -> dict[str, Any]:
    """Execute a query via API."""
    query = data.get("query")
    if not query:
        return _api_response(400, {"error": "Query string required"})

    # Optional parameters
    database = data.get("database")
    workgroup = data.get("workgroup")
    wait = data.get("wait", False)
    timeout = data.get("timeout", settings.athena_query_timeout)

    # Execute query
    execution = athena_service.execute_query(
        query=query,
        database=database,
        workgroup=workgroup,
        wait=wait,
        timeout=timeout,
    )

    response_data = {
        "query_execution_id": execution.query_execution_id,
        "state": execution.state.value,
        "database": execution.database,
    }

    # If waited for completion and succeeded, include result summary
    if wait and execution.state == QueryState.SUCCEEDED:
        response_data["execution_time_ms"] = execution.execution_time_ms
        response_data["data_scanned_bytes"] = execution.data_scanned_bytes
        response_data["output_location"] = execution.output_location

        # Optionally include results if requested
        if data.get("include_results", False):
            max_results = data.get("max_results", 100)
            results = athena_service.get_query_results(
                execution.query_execution_id, max_results=max_results
            )
            response_data["results"] = {
                "columns": results.columns,
                "rows": results.rows,
                "total_rows": results.total_rows,
                "has_more": results.next_token is not None,
            }

    return _api_response(200 if wait else 202, response_data)


def _get_query_status_api(
    data: dict[str, Any], event: dict[str, Any], athena_service: Any
) -> dict[str, Any]:
    """Get query execution status via API."""
    query_execution_id = data.get("query_execution_id") or _get_path_param(
        event, "query_execution_id"
    )
    if not query_execution_id:
        return _api_response(400, {"error": "query_execution_id required"})

    execution = athena_service.get_query_execution(query_execution_id)

    return _api_response(
        200,
        {
            "query_execution_id": execution.query_execution_id,
            "state": execution.state.value,
            "state_change_reason": execution.state_change_reason,
            "submission_time": execution.submission_time.isoformat(),
            "completion_time": execution.completion_time.isoformat()
            if execution.completion_time
            else None,
            "execution_time_ms": execution.execution_time_ms,
            "data_scanned_bytes": execution.data_scanned_bytes,
        },
    )


def _get_query_results_api(
    data: dict[str, Any], event: dict[str, Any], athena_service: Any
) -> dict[str, Any]:
    """Get query results via API."""
    query_execution_id = data.get("query_execution_id") or _get_path_param(
        event, "query_execution_id"
    )
    if not query_execution_id:
        return _api_response(400, {"error": "query_execution_id required"})

    max_results = data.get("max_results", 1000)
    next_token = data.get("next_token")

    results = athena_service.get_query_results(
        query_execution_id, max_results=max_results, next_token=next_token
    )

    return _api_response(
        200,
        {
            "query_execution_id": results.query_execution_id,
            "columns": results.columns,
            "rows": results.rows,
            "total_rows": results.total_rows,
            "next_token": results.next_token,
        },
    )


def _cancel_query_api(
    data: dict[str, Any], event: dict[str, Any], athena_service: Any
) -> dict[str, Any]:
    """Cancel a running query via API."""
    query_execution_id = data.get("query_execution_id") or _get_path_param(
        event, "query_execution_id"
    )
    if not query_execution_id:
        return _api_response(400, {"error": "query_execution_id required"})

    athena_service.cancel_query(query_execution_id)

    return _api_response(
        200, {"status": "cancelled", "query_execution_id": query_execution_id}
    )


def _get_query_metrics_api(
    data: dict[str, Any], event: dict[str, Any], athena_service: Any
) -> dict[str, Any]:
    """Get query performance metrics via API."""
    query_execution_id = data.get("query_execution_id") or _get_path_param(
        event, "query_execution_id"
    )
    if not query_execution_id:
        return _api_response(400, {"error": "query_execution_id required"})

    metrics = athena_service.get_query_metrics(query_execution_id)

    return _api_response(
        200,
        {
            "query_execution_id": metrics.query_execution_id,
            "data_scanned_bytes": metrics.data_scanned_bytes,
            "data_scanned_gb": metrics.data_scanned_gb,
            "execution_time_ms": metrics.execution_time_ms,
            "estimated_cost_usd": metrics.estimated_cost_usd,
        },
    )


def _handle_direct_invocation(event: dict[str, Any]) -> dict[str, Any]:
    """Handle direct Lambda invocation for queries."""
    athena_service = get_athena_service()

    action = event.get("action", "execute")

    if action == "execute":
        query = event.get("query")
        if not query:
            return {"status": "error", "message": "Query string required"}

        execution = athena_service.execute_query(
            query=query,
            database=event.get("database"),
            workgroup=event.get("workgroup"),
            wait=event.get("wait", True),
            timeout=event.get("timeout", settings.athena_query_timeout),
        )

        result = {
            "query_execution_id": execution.query_execution_id,
            "state": execution.state.value,
            "database": execution.database,
        }

        # Include results if query succeeded
        if execution.state == QueryState.SUCCEEDED:
            result["execution_time_ms"] = execution.execution_time_ms
            result["data_scanned_bytes"] = execution.data_scanned_bytes

            if event.get("include_results", True):
                results = athena_service.get_query_results(
                    execution.query_execution_id,
                    max_results=event.get("max_results", 1000),
                )
                result["columns"] = results.columns
                result["rows"] = results.rows
                result["total_rows"] = results.total_rows

        return result

    elif action == "status":
        query_execution_id = event.get("query_execution_id")
        execution = athena_service.get_query_execution(query_execution_id)

        return {
            "query_execution_id": execution.query_execution_id,
            "state": execution.state.value,
            "state_change_reason": execution.state_change_reason,
            "execution_time_ms": execution.execution_time_ms,
            "data_scanned_bytes": execution.data_scanned_bytes,
        }

    elif action == "results":
        query_execution_id = event.get("query_execution_id")
        results = athena_service.get_query_results(
            query_execution_id,
            max_results=event.get("max_results", 1000),
            next_token=event.get("next_token"),
        )

        return {
            "columns": results.columns,
            "rows": results.rows,
            "total_rows": results.total_rows,
            "next_token": results.next_token,
        }

    elif action == "cancel":
        query_execution_id = event.get("query_execution_id")
        athena_service.cancel_query(query_execution_id)
        return {"status": "cancelled", "query_execution_id": query_execution_id}

    elif action == "metrics":
        query_execution_id = event.get("query_execution_id")
        metrics = athena_service.get_query_metrics(query_execution_id)

        return {
            "data_scanned_bytes": metrics.data_scanned_bytes,
            "data_scanned_gb": metrics.data_scanned_gb,
            "execution_time_ms": metrics.execution_time_ms,
            "estimated_cost_usd": metrics.estimated_cost_usd,
        }

    elif action == "list":
        workgroup = event.get("workgroup")
        max_results = event.get("max_results", 50)
        execution_ids = athena_service.list_query_executions(workgroup, max_results)
        return {"query_execution_ids": execution_ids}

    return {"status": "error", "message": f"Unknown action: {action}"}


def _get_path_param(event: dict[str, Any], param: str) -> str | None:
    """Extract path parameter from API Gateway event."""
    path_params = event.get("pathParameters", {}) or {}
    return path_params.get(param)


def _api_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Create API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body, default=str),
    }


def _error_response(
    status_code: int, message: str, query_execution_id: str | None = None
) -> dict[str, Any]:
    """Create error response."""
    body: dict[str, Any] = {"error": message}
    if query_execution_id:
        body["query_execution_id"] = query_execution_id
    return _api_response(status_code, body)
