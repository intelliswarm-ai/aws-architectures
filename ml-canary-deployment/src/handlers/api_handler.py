"""API Gateway handler for real-time inference requests."""

import time
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import InferenceError, ValidationError
from src.common.models import ContentType, InferenceRequest, InferenceResponse
from src.common.utils import generate_request_id, json_deserialize, json_serialize
from src.services.inference_service import InferenceService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Handle API Gateway requests for real-time inference.

    Processes recommendation requests and invokes the SageMaker endpoint,
    which automatically routes to the appropriate production variant based
    on configured traffic weights.

    Args:
        event: API Gateway event containing the inference request.
        context: Lambda context object.

    Returns:
        API Gateway response with inference results.
    """
    start_time = time.perf_counter()
    request_id = event.get("requestContext", {}).get("requestId", generate_request_id())

    logger.info("Processing inference request", request_id=request_id)

    try:
        # Parse and validate request
        body = _parse_request_body(event)
        inference_request = _build_inference_request(body, request_id)

        # Get services
        settings = get_settings()
        clients = get_clients()
        inference_service = InferenceService(clients, settings)

        # Invoke endpoint
        response = inference_service.invoke_endpoint(inference_request)

        # Calculate total latency
        total_latency_ms = (time.perf_counter() - start_time) * 1000

        # Build response
        inference_response = InferenceResponse(
            request_id=request_id,
            predictions=response["predictions"],
            variant_name=response["variant_name"],
            model_latency_ms=response["model_latency_ms"],
            total_latency_ms=total_latency_ms,
        )

        logger.info(
            "Inference completed",
            request_id=request_id,
            variant_name=inference_response.variant_name,
            model_latency_ms=inference_response.model_latency_ms,
            total_latency_ms=total_latency_ms,
        )

        return _build_success_response(inference_response)

    except ValidationError as e:
        logger.warning("Validation error", request_id=request_id, error=str(e))
        return _build_error_response(400, e.message, request_id)

    except InferenceError as e:
        logger.error(
            "Inference error",
            request_id=request_id,
            variant_name=e.variant_name,
            error=str(e),
        )
        return _build_error_response(502, e.message, request_id)

    except Exception as e:
        logger.exception("Unexpected error", request_id=request_id)
        return _build_error_response(500, "Internal server error", request_id)


def _parse_request_body(event: dict[str, Any]) -> dict[str, Any]:
    """Parse and validate request body.

    Args:
        event: API Gateway event.

    Returns:
        Parsed request body.

    Raises:
        ValidationError: If body is missing or invalid.
    """
    body = event.get("body")
    if not body:
        raise ValidationError("Request body is required")

    try:
        if isinstance(body, str):
            return json_deserialize(body)
        return body
    except Exception as e:
        raise ValidationError(f"Invalid JSON in request body: {e}")


def _build_inference_request(body: dict[str, Any], request_id: str) -> InferenceRequest:
    """Build InferenceRequest from parsed body.

    Args:
        body: Parsed request body.
        request_id: Request identifier.

    Returns:
        Validated InferenceRequest.

    Raises:
        ValidationError: If required fields are missing.
    """
    try:
        user_id = body.get("user_id")
        if not user_id:
            raise ValidationError("user_id is required")

        features = body.get("features", {})
        if not features:
            raise ValidationError("features dictionary is required")

        content_type = body.get("content_type", ContentType.JSON.value)
        target_variant = body.get("target_variant")

        return InferenceRequest(
            request_id=request_id,
            user_id=user_id,
            features=features,
            content_type=ContentType(content_type),
            target_variant=target_variant,
        )
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError(f"Invalid request format: {e}")


def _build_success_response(response: InferenceResponse) -> dict[str, Any]:
    """Build API Gateway success response.

    Args:
        response: Inference response model.

    Returns:
        API Gateway response dictionary.
    """
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "X-Request-Id": response.request_id,
            "X-Variant-Name": response.variant_name,
            "X-Model-Latency-Ms": str(response.model_latency_ms),
        },
        "body": json_serialize(response.model_dump()),
    }


def _build_error_response(
    status_code: int, message: str, request_id: str
) -> dict[str, Any]:
    """Build API Gateway error response.

    Args:
        status_code: HTTP status code.
        message: Error message.
        request_id: Request identifier.

    Returns:
        API Gateway response dictionary.
    """
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "X-Request-Id": request_id,
        },
        "body": json_serialize({
            "error": message,
            "request_id": request_id,
        }),
    }
