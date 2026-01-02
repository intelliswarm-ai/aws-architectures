"""Lambda handler for API Gateway requests.

This is the main entry point for all API Gateway requests,
routing to appropriate handlers based on path and method.
"""

import json
import logging
from typing import Any

from ..common.config import settings
from ..services import (
    get_athena_service,
    get_glue_service,
    get_lakeformation_service,
    get_s3_service,
)

logger = logging.getLogger()
logger.setLevel(settings.log_level)


def handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle API Gateway requests.

    Routes:
        POST /ingest - Ingest JSON documents
        POST /etl - Trigger ETL job
        GET  /etl/{job_run_id} - Get ETL job status
        POST /query - Execute Athena query
        GET  /query/{query_execution_id} - Get query status
        GET  /query/{query_execution_id}/results - Get query results
        DELETE /query/{query_execution_id} - Cancel query
        GET  /tables - List tables in catalog
        GET  /tables/{table_name} - Get table details
        GET  /partitions - Get partition statistics
        GET  /health - Health check

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    logger.info(f"API request: {event.get('httpMethod')} {event.get('path')}")

    try:
        http_method = event.get("httpMethod", "GET")
        path = event.get("path", "/")
        path_params = event.get("pathParameters", {}) or {}
        query_params = event.get("queryStringParameters", {}) or {}

        # Parse request body
        body = _parse_body(event)

        # Route request
        if path == "/health":
            return _health_check()

        elif path.startswith("/ingest"):
            return _handle_ingest(body)

        elif path.startswith("/etl"):
            return _handle_etl(http_method, path_params, body)

        elif path.startswith("/query"):
            return _handle_query(http_method, path, path_params, query_params, body)

        elif path.startswith("/tables"):
            return _handle_tables(http_method, path_params, query_params)

        elif path.startswith("/partitions"):
            return _handle_partitions(query_params)

        elif path.startswith("/permissions"):
            return _handle_permissions(http_method, body)

        else:
            return _api_response(404, {"error": f"Not found: {path}"})

    except json.JSONDecodeError as e:
        return _api_response(400, {"error": f"Invalid JSON: {e}"})
    except Exception as e:
        logger.exception(f"API error: {e}")
        return _api_response(500, {"error": str(e)})


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    """Parse request body from event."""
    body = event.get("body", "")
    if not body:
        return {}

    if event.get("isBase64Encoded"):
        import base64

        body = base64.b64decode(body).decode("utf-8")

    return json.loads(body) if body else {}


def _health_check() -> dict[str, Any]:
    """Return health check response."""
    return _api_response(
        200,
        {
            "status": "healthy",
            "service": "aws-athena-datalake",
            "region": settings.aws_region,
            "database": settings.glue_database,
        },
    )


def _handle_ingest(body: dict[str, Any]) -> dict[str, Any]:
    """Handle data ingestion requests."""
    from ..common.models import EventDocument, PartitionSpec

    s3_service = get_s3_service()

    documents = body.get("documents", [])
    if not documents:
        return _api_response(400, {"error": "No documents provided"})

    # Parse documents
    event_docs = []
    errors = []
    for i, doc in enumerate(documents):
        try:
            event_docs.append(EventDocument(**doc))
        except Exception as e:
            errors.append({"index": i, "error": str(e)})

    if not event_docs:
        return _api_response(400, {"error": "No valid documents", "details": errors})

    # Determine partition
    partition = None
    if "partition" in body:
        partition = PartitionSpec(**body["partition"])

    result = s3_service.write_json_documents(event_docs, partition)

    return _api_response(
        200,
        {
            "status": "success",
            "records_written": result.records_written,
            "bytes_written": result.bytes_written,
            "s3_location": f"s3://{result.bucket}/{result.s3_key}",
            "partition": result.partition.path,
            "errors": errors if errors else None,
        },
    )


def _handle_etl(
    http_method: str, path_params: dict[str, str], body: dict[str, Any]
) -> dict[str, Any]:
    """Handle ETL job requests."""
    from ..common.models import PartitionSpec
    from datetime import datetime

    glue_service = get_glue_service()

    if http_method == "POST":
        # Start ETL job
        partition = None
        if "partition" in body:
            partition = PartitionSpec(**body["partition"])
        else:
            partition = PartitionSpec.from_datetime(datetime.utcnow())

        job_arguments = {
            "--partition_year": partition.year,
            "--partition_month": partition.month,
            "--partition_day": partition.day,
            "--partition_hour": partition.hour or "00",
        }

        job_run_id = glue_service.start_etl_job(arguments=job_arguments)

        return _api_response(
            202,
            {
                "status": "started",
                "job_run_id": job_run_id,
                "partition": partition.path,
            },
        )

    elif http_method == "GET":
        job_run_id = path_params.get("job_run_id")
        if not job_run_id:
            return _api_response(400, {"error": "job_run_id required"})

        job_run = glue_service.get_job_run(job_run_id)

        return _api_response(
            200,
            {
                "job_run_id": job_run_id,
                "status": job_run.status.value,
                "started_on": job_run.started_on.isoformat(),
                "completed_on": job_run.completed_on.isoformat()
                if job_run.completed_on
                else None,
                "execution_time_seconds": job_run.execution_time_seconds,
                "error_message": job_run.error_message,
            },
        )

    return _api_response(405, {"error": f"Method not allowed: {http_method}"})


def _handle_query(
    http_method: str,
    path: str,
    path_params: dict[str, str],
    query_params: dict[str, str],
    body: dict[str, Any],
) -> dict[str, Any]:
    """Handle Athena query requests."""
    from ..common.models import QueryState

    athena_service = get_athena_service()

    if http_method == "POST" and path == "/query":
        # Execute new query
        query = body.get("query")
        if not query:
            return _api_response(400, {"error": "Query string required"})

        wait = body.get("wait", False)
        execution = athena_service.execute_query(
            query=query,
            database=body.get("database"),
            workgroup=body.get("workgroup"),
            wait=wait,
            timeout=body.get("timeout", settings.athena_query_timeout),
        )

        response_data = {
            "query_execution_id": execution.query_execution_id,
            "state": execution.state.value,
        }

        if wait and execution.state == QueryState.SUCCEEDED:
            response_data["execution_time_ms"] = execution.execution_time_ms
            response_data["data_scanned_bytes"] = execution.data_scanned_bytes

        return _api_response(200 if wait else 202, response_data)

    elif http_method == "GET":
        query_execution_id = path_params.get("query_execution_id")
        if not query_execution_id:
            return _api_response(400, {"error": "query_execution_id required"})

        if "/results" in path:
            # Get query results
            max_results = int(query_params.get("max_results", "1000"))
            next_token = query_params.get("next_token")

            results = athena_service.get_query_results(
                query_execution_id, max_results=max_results, next_token=next_token
            )

            return _api_response(
                200,
                {
                    "columns": results.columns,
                    "rows": results.rows,
                    "total_rows": results.total_rows,
                    "next_token": results.next_token,
                },
            )

        elif "/metrics" in path:
            # Get query metrics
            metrics = athena_service.get_query_metrics(query_execution_id)

            return _api_response(
                200,
                {
                    "data_scanned_bytes": metrics.data_scanned_bytes,
                    "data_scanned_gb": metrics.data_scanned_gb,
                    "execution_time_ms": metrics.execution_time_ms,
                    "estimated_cost_usd": metrics.estimated_cost_usd,
                },
            )

        else:
            # Get query status
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
                },
            )

    elif http_method == "DELETE":
        query_execution_id = path_params.get("query_execution_id")
        if not query_execution_id:
            return _api_response(400, {"error": "query_execution_id required"})

        athena_service.cancel_query(query_execution_id)
        return _api_response(
            200, {"status": "cancelled", "query_execution_id": query_execution_id}
        )

    return _api_response(405, {"error": f"Method not allowed: {http_method}"})


def _handle_tables(
    http_method: str, path_params: dict[str, str], query_params: dict[str, str]
) -> dict[str, Any]:
    """Handle table metadata requests."""
    glue_service = get_glue_service()

    table_name = path_params.get("table_name")

    if table_name:
        # Get specific table details
        table = glue_service.get_table(
            table_name, database=query_params.get("database")
        )

        return _api_response(
            200,
            {
                "name": table["Name"],
                "database": table["DatabaseName"],
                "columns": [
                    {"name": col["Name"], "type": col["Type"]}
                    for col in table.get("StorageDescriptor", {}).get("Columns", [])
                ],
                "partition_keys": [
                    {"name": pk["Name"], "type": pk["Type"]}
                    for pk in table.get("PartitionKeys", [])
                ],
                "location": table.get("StorageDescriptor", {}).get("Location"),
                "table_type": table.get("TableType"),
            },
        )

    # List tables would require additional Glue API call
    return _api_response(
        200,
        {
            "database": settings.glue_database,
            "message": "Use GET /tables/{table_name} to get table details",
        },
    )


def _handle_partitions(query_params: dict[str, str]) -> dict[str, Any]:
    """Handle partition statistics requests."""
    s3_service = get_s3_service()

    prefix = query_params.get("prefix", "processed/")
    bucket = query_params.get("bucket")

    partition_sizes = s3_service.get_partition_sizes(prefix, bucket)

    # Calculate statistics
    total_size = sum(partition_sizes.values())
    partition_count = len(partition_sizes)

    return _api_response(
        200,
        {
            "total_size_bytes": total_size,
            "total_size_gb": total_size / (1024**3),
            "partition_count": partition_count,
            "partitions": partition_sizes,
        },
    )


def _handle_permissions(http_method: str, body: dict[str, Any]) -> dict[str, Any]:
    """Handle Lake Formation permission requests."""
    from ..common.models import PermissionType

    lf_service = get_lakeformation_service()

    if http_method == "GET":
        principal = body.get("principal")
        permissions = lf_service.list_permissions(principal_arn=principal)

        return _api_response(
            200,
            {
                "permissions": [
                    {
                        "principal": p.principal,
                        "resource_type": p.resource_type,
                        "resource_arn": p.resource_arn,
                        "permissions": [perm.value for perm in p.permissions],
                    }
                    for p in permissions
                ]
            },
        )

    elif http_method == "POST":
        # Grant permission
        principal = body.get("principal")
        resource_type = body.get("resource_type")
        resource_name = body.get("resource_name")
        permissions = body.get("permissions", ["SELECT"])

        if not principal or not resource_type or not resource_name:
            return _api_response(
                400, {"error": "principal, resource_type, resource_name required"}
            )

        perm_types = [PermissionType(p) for p in permissions]

        if resource_type == "TABLE":
            lf_service.grant_table_permissions(
                principal, resource_name, permissions=perm_types
            )
        elif resource_type == "DATABASE":
            lf_service.grant_database_permissions(principal, permissions=perm_types)

        return _api_response(200, {"status": "granted"})

    return _api_response(405, {"error": f"Method not allowed: {http_method}"})


def _api_response(status_code: int, body: dict[str, Any]) -> dict[str, Any]:
    """Create API Gateway response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": json.dumps(body, default=str),
    }
