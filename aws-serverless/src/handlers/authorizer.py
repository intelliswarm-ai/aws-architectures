"""Custom Lambda Authorizer for API Gateway.

This authorizer validates JWT tokens from Cognito and generates IAM policies
for API Gateway. It supports caching via the authorization token.
"""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.exceptions import AuthenticationError
from src.common.security import generate_policy, get_jwt_validator

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda authorizer handler for API Gateway.

    Validates JWT tokens and returns an IAM policy allowing or denying access.

    Args:
        event: Authorizer event with token and methodArn
        context: Lambda context

    Returns:
        IAM policy document
    """
    logger.info("Processing authorization request")

    try:
        # Extract token from Authorization header
        token = extract_token(event)
        if not token:
            logger.warning("No token provided")
            raise AuthenticationError("No authorization token provided")

        # Validate token and get claims
        validator = get_jwt_validator()
        claims = validator.validate_token(token)

        # Extract tenant context for downstream handlers
        tenant_context = validator.extract_tenant_context(claims)

        logger.info(
            "Token validated successfully",
            extra={
                "user_id": tenant_context.user_id,
                "tenant_id": tenant_context.tenant_id,
                "roles": tenant_context.roles,
            },
        )

        # Generate allow policy with context
        method_arn = event.get("methodArn", "*")
        resource = build_resource_arn(method_arn)

        return generate_policy(
            principal_id=tenant_context.user_id,
            effect="Allow",
            resource=resource,
            context={
                "tenant_id": tenant_context.tenant_id,
                "user_id": tenant_context.user_id,
                "email": tenant_context.email or "",
                "roles": tenant_context.roles,
                "permissions": tenant_context.permissions,
                "tier": tenant_context.tier.value,
            },
        )

    except AuthenticationError as e:
        logger.warning(f"Authentication failed: {e.message}")
        # Return deny policy for invalid tokens
        return generate_policy(
            principal_id="unauthorized",
            effect="Deny",
            resource=event.get("methodArn", "*"),
        )

    except Exception as e:
        logger.exception(f"Unexpected error in authorizer: {e}")
        # Return deny policy for any other errors
        return generate_policy(
            principal_id="error",
            effect="Deny",
            resource=event.get("methodArn", "*"),
        )


def extract_token(event: dict[str, Any]) -> str | None:
    """Extract JWT token from authorizer event.

    Args:
        event: Authorizer event

    Returns:
        JWT token or None
    """
    # Token-based authorizer
    if "authorizationToken" in event:
        auth_header = event["authorizationToken"]
        if auth_header.lower().startswith("bearer "):
            return auth_header[7:]
        return auth_header

    # Request-based authorizer
    headers = event.get("headers", {}) or {}
    auth_header = headers.get("Authorization") or headers.get("authorization", "")

    if auth_header.lower().startswith("bearer "):
        return auth_header[7:]

    return None


def build_resource_arn(method_arn: str) -> str:
    """Build a wildcard resource ARN for the policy.

    Allows access to all methods on the API stage.

    Args:
        method_arn: The specific method ARN from the request

    Returns:
        Wildcard ARN for the API stage
    """
    if method_arn == "*":
        return "*"

    # Parse: arn:aws:execute-api:region:account:api-id/stage/method/path
    parts = method_arn.split(":")
    if len(parts) < 6:
        return method_arn

    api_parts = parts[5].split("/")
    if len(api_parts) < 2:
        return method_arn

    # Build wildcard: arn:aws:execute-api:region:account:api-id/stage/*
    api_id = api_parts[0]
    stage = api_parts[1]

    return f"{':'.join(parts[:5])}:{api_id}/{stage}/*"
