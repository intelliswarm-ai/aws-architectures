"""API Gateway Lambda Handler with multi-tenant support.

This handler processes API Gateway requests with Cognito authentication,
extracting tenant context and routing to appropriate business logic.
"""

from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.exceptions import (
    AuthenticationError,
    AuthorizationError,
    BaseError,
    ResourceNotFoundError,
    ValidationError,
)
from src.common.models import TenantContext, TenantTier
from src.common.security import Authorizer
from src.common.utils import (
    build_api_response,
    error_response,
    generate_request_id,
    json_loads,
    parse_api_gateway_event,
    success_response,
)

logger = Logger()
tracer = Tracer()
metrics = Metrics()

settings = get_settings()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Main API Gateway handler with multi-tenant support.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response
    """
    request_id = generate_request_id()
    logger.append_keys(request_id=request_id)

    try:
        # Parse the API Gateway event
        parsed = parse_api_gateway_event(event)
        method = parsed["method"]
        path = parsed["path"]

        logger.info(f"Processing {method} {path}")

        # Extract tenant context from authorizer
        tenant_context = extract_tenant_context(event)
        if not tenant_context:
            raise AuthenticationError("Missing authorization context")

        logger.append_keys(
            tenant_id=tenant_context.tenant_id,
            user_id=tenant_context.user_id,
        )

        # Create authorizer for permission checks
        auth = Authorizer(tenant_context)

        # Route to appropriate handler
        response_data = route_request(
            method=method,
            path=path,
            parsed_event=parsed,
            tenant_context=tenant_context,
            auth=auth,
        )

        # Add metrics
        metrics.add_metric(name="ApiRequests", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="Tenant", value=tenant_context.tenant_id)
        metrics.add_dimension(name="Method", value=method)

        return success_response(data=response_data)

    except ValidationError as e:
        logger.warning(f"Validation error: {e.message}")
        metrics.add_metric(name="ValidationErrors", unit=MetricUnit.Count, value=1)
        return error_response(400, e.error_code, e.message, e.details)

    except AuthenticationError as e:
        logger.warning(f"Authentication error: {e.message}")
        metrics.add_metric(name="AuthenticationErrors", unit=MetricUnit.Count, value=1)
        return error_response(401, e.error_code, e.message)

    except AuthorizationError as e:
        logger.warning(f"Authorization error: {e.message}")
        metrics.add_metric(name="AuthorizationErrors", unit=MetricUnit.Count, value=1)
        return error_response(403, e.error_code, e.message, e.details)

    except ResourceNotFoundError as e:
        logger.warning(f"Resource not found: {e.message}")
        return error_response(404, e.error_code, e.message, e.details)

    except BaseError as e:
        logger.error(f"Application error: {e.message}")
        metrics.add_metric(name="ApplicationErrors", unit=MetricUnit.Count, value=1)
        return error_response(500, e.error_code, e.message)

    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        metrics.add_metric(name="UnexpectedErrors", unit=MetricUnit.Count, value=1)
        return error_response(500, "INTERNAL_ERROR", "An unexpected error occurred")


def extract_tenant_context(event: dict[str, Any]) -> TenantContext | None:
    """Extract tenant context from API Gateway authorizer context.

    Args:
        event: API Gateway event

    Returns:
        TenantContext or None if not found
    """
    request_context = event.get("requestContext", {})
    authorizer = request_context.get("authorizer", {})

    # For Cognito User Pool authorizer
    claims = authorizer.get("claims", {})
    if claims:
        tenant_id = claims.get("custom:tenant_id")
        if tenant_id:
            return TenantContext(
                tenant_id=tenant_id,
                user_id=claims.get("sub", ""),
                email=claims.get("email"),
                roles=_parse_list(claims.get("cognito:groups", [])),
                tier=_parse_tier(claims.get("custom:tier", "free")),
            )

    # For Lambda authorizer
    tenant_id = authorizer.get("tenant_id")
    if tenant_id:
        return TenantContext(
            tenant_id=tenant_id,
            user_id=authorizer.get("user_id", ""),
            email=authorizer.get("email"),
            roles=_parse_list(authorizer.get("roles", [])),
            permissions=_parse_list(authorizer.get("permissions", [])),
            tier=_parse_tier(authorizer.get("tier", "free")),
        )

    return None


def _parse_list(value: Any) -> list[str]:
    """Parse a value that might be a JSON string or list."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json_loads(value)
            return parsed if isinstance(parsed, list) else [value]
        except Exception:
            return [value] if value else []
    return []


def _parse_tier(value: str) -> TenantTier:
    """Parse tier string to enum."""
    try:
        return TenantTier(value.lower())
    except ValueError:
        return TenantTier.FREE


@tracer.capture_method
def route_request(
    method: str,
    path: str,
    parsed_event: dict[str, Any],
    tenant_context: TenantContext,
    auth: Authorizer,
) -> Any:
    """Route API request to appropriate handler.

    Args:
        method: HTTP method
        path: Request path
        parsed_event: Parsed event data
        tenant_context: Tenant context
        auth: Authorizer instance

    Returns:
        Response data
    """
    # Example routes - extend based on your API design
    path_parts = path.strip("/").split("/")

    if len(path_parts) >= 1:
        resource = path_parts[0]

        if resource == "tenants":
            return handle_tenants(method, path_parts, parsed_event, tenant_context, auth)

        if resource == "resources":
            return handle_resources(method, path_parts, parsed_event, tenant_context, auth)

        if resource == "health":
            return {"status": "healthy", "environment": settings.environment}

    raise ResourceNotFoundError("endpoint", path)


@tracer.capture_method
def handle_tenants(
    method: str,
    path_parts: list[str],
    parsed_event: dict[str, Any],
    tenant_context: TenantContext,
    auth: Authorizer,
) -> Any:
    """Handle tenant-related API requests."""
    # GET /tenants - list tenants (admin only)
    if method == "GET" and len(path_parts) == 1:
        auth.require_role("admin")
        return {"tenants": [], "message": "Tenant list endpoint"}

    # GET /tenants/{id} - get tenant details
    if method == "GET" and len(path_parts) == 2:
        tenant_id = path_parts[1]
        if not auth.can_access_tenant(tenant_id):
            raise AuthorizationError("Cannot access this tenant's data")
        return {
            "tenant_id": tenant_id,
            "message": "Tenant details endpoint",
        }

    # POST /tenants - create tenant (admin only)
    if method == "POST" and len(path_parts) == 1:
        auth.require_role("admin")
        body = parsed_event.get("body", {})
        return {"message": "Tenant created", "data": body}

    raise ResourceNotFoundError("tenant endpoint", "/".join(path_parts))


@tracer.capture_method
def handle_resources(
    method: str,
    path_parts: list[str],
    parsed_event: dict[str, Any],
    tenant_context: TenantContext,
    auth: Authorizer,
) -> Any:
    """Handle resource-related API requests."""
    # All resource operations require at least read permission
    auth.require_permission("read")

    # GET /resources - list resources
    if method == "GET" and len(path_parts) == 1:
        return {
            "resources": [],
            "tenant_id": tenant_context.tenant_id,
            "message": "Resource list for tenant",
        }

    # GET /resources/{id} - get resource
    if method == "GET" and len(path_parts) == 2:
        resource_id = path_parts[1]
        return {
            "resource_id": resource_id,
            "tenant_id": tenant_context.tenant_id,
        }

    # POST /resources - create resource
    if method == "POST" and len(path_parts) == 1:
        auth.require_permission("write")
        body = parsed_event.get("body", {})
        return {
            "message": "Resource created",
            "tenant_id": tenant_context.tenant_id,
            "data": body,
        }

    # PUT /resources/{id} - update resource
    if method == "PUT" and len(path_parts) == 2:
        auth.require_permission("write")
        resource_id = path_parts[1]
        body = parsed_event.get("body", {})
        return {
            "message": "Resource updated",
            "resource_id": resource_id,
            "data": body,
        }

    # DELETE /resources/{id} - delete resource
    if method == "DELETE" and len(path_parts) == 2:
        auth.require_permission("delete")
        # Enterprise tier required for delete
        auth.require_tier(TenantTier.PROFESSIONAL)
        resource_id = path_parts[1]
        return {
            "message": "Resource deleted",
            "resource_id": resource_id,
        }

    raise ResourceNotFoundError("resource endpoint", "/".join(path_parts))
