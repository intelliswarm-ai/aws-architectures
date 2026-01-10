"""Bedrock Agent handler for conversational interactions."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.config import get_settings
from src.common.exceptions import AgentError, ValidationError
from src.common.models import AgentRequest, AgentResponse, ApiResponse
from src.services.agent_service import AgentService

logger = Logger()
tracer = Tracer()
metrics = Metrics()

settings = get_settings()
agent_service = AgentService()


@tracer.capture_method
def process_agent_request(event: dict[str, Any]) -> dict[str, Any]:
    """Process an agent interaction request."""
    try:
        # Parse request
        request = AgentRequest(**event)

        logger.info(
            "Processing agent request",
            input_length=len(request.input_text),
            session_id=request.session_id,
        )

        # Invoke agent
        response = agent_service.invoke(request)

        # Record metrics
        metrics.add_metric(name="AgentInvocations", unit="Count", value=1)
        metrics.add_metric(name="AgentActions", unit="Count", value=len(response.actions))
        metrics.add_metric(name="AgentCitations", unit="Count", value=len(response.citations))

        return ApiResponse(
            success=True,
            data=response.model_dump(by_alias=True),
        ).model_dump(by_alias=True)

    except ValidationError as e:
        logger.warning("Validation error", error=e.message)
        metrics.add_metric(name="AgentValidationErrors", unit="Count", value=1)
        return ApiResponse(
            success=False,
            error=e.message,
            error_code=e.error_code,
        ).model_dump(by_alias=True)

    except AgentError as e:
        logger.error("Agent error", error=e.message, details=e.details)
        metrics.add_metric(name="AgentErrors", unit="Count", value=1)
        return ApiResponse(
            success=False,
            error=e.message,
            error_code=e.error_code,
        ).model_dump(by_alias=True)

    except Exception as e:
        logger.exception("Unexpected error in agent invocation")
        metrics.add_metric(name="AgentUnexpectedErrors", unit="Count", value=1)
        return ApiResponse(
            success=False,
            error=str(e),
            error_code="INTERNAL_ERROR",
        ).model_dump(by_alias=True)


@tracer.capture_method
def process_api_gateway_event(event: dict[str, Any]) -> dict[str, Any]:
    """Process API Gateway event for agent interaction."""
    try:
        body = json.loads(event.get("body", "{}"))
        request = AgentRequest(**body)

        logger.info(
            "Processing API Gateway agent request",
            input_length=len(request.input_text),
        )

        response = agent_service.invoke(request)

        metrics.add_metric(name="APIAgentInvocations", unit="Count", value=1)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps(
                ApiResponse(
                    success=True,
                    data=response.model_dump(by_alias=True),
                ).model_dump(by_alias=True)
            ),
        }

    except ValidationError as e:
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                ApiResponse(
                    success=False,
                    error=e.message,
                    error_code=e.error_code,
                ).model_dump(by_alias=True)
            ),
        }

    except AgentError as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                ApiResponse(
                    success=False,
                    error=e.message,
                    error_code=e.error_code,
                ).model_dump(by_alias=True)
            ),
        }

    except Exception as e:
        logger.exception("Unexpected error")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                ApiResponse(
                    success=False,
                    error="Internal server error",
                    error_code="INTERNAL_ERROR",
                ).model_dump(by_alias=True)
            ),
        }


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Lambda handler for Bedrock Agent interactions.

    Supports:
    - API Gateway events
    - Direct Lambda invocation
    """
    # Check if this is an API Gateway event
    if "httpMethod" in event or "requestContext" in event:
        return process_api_gateway_event(event)

    # Direct invocation
    return process_agent_request(event)
