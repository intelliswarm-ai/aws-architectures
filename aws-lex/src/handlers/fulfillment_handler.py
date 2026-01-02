"""Main Lex fulfillment handler that routes to intent-specific handlers."""

from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from ..common.exceptions import LexBotError
from ..common.models import LexEvent
from ..services.lex_response_service import LexResponseService
from .book_flight_handler import handle_book_flight
from .check_in_handler import handle_check_in
from .update_booking_handler import handle_update_booking

logger = Logger()
tracer = Tracer()

INTENT_HANDLERS = {
    "BookFlight": handle_book_flight,
    "UpdateBooking": handle_update_booking,
    "CheckIn": handle_check_in,
}


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Main Lambda handler for Lex fulfillment.

    Routes incoming Lex events to the appropriate intent handler.

    Args:
        event: Lex V2 event
        context: Lambda context

    Returns:
        Lex response
    """
    logger.info("Received Lex event", extra={"event": event})

    try:
        lex_event = LexEvent(**event)
        intent_name = lex_event.get_intent_name()
        invocation_source = lex_event.invocation_source

        logger.info(
            "Processing intent",
            extra={"intent": intent_name, "invocation_source": invocation_source},
        )

        handler_func = INTENT_HANDLERS.get(intent_name)

        if not handler_func:
            logger.warning(f"Unknown intent: {intent_name}")
            return _build_fallback_response(intent_name)

        return handler_func(lex_event)

    except LexBotError as e:
        logger.error(f"Business error: {e.message}", extra={"error_code": e.error_code})
        return _build_error_response(event, str(e.message))

    except Exception as e:
        logger.exception("Unexpected error processing Lex event")
        return _build_error_response(event, "Sorry, something went wrong. Please try again.")


def _build_fallback_response(intent_name: str) -> dict[str, Any]:
    """Build a fallback response for unknown intents."""
    return LexResponseService.build_fulfillment_response(
        intent_name=intent_name,
        message=(
            "I'm not sure how to help with that. "
            "I can help you book a flight, update a booking, or check in for your flight."
        ),
        fulfilled=False,
    )


def _build_error_response(event: dict[str, Any], message: str) -> dict[str, Any]:
    """Build an error response."""
    intent_name = ""
    if event.get("sessionState", {}).get("intent"):
        intent_name = event["sessionState"]["intent"].get("name", "")

    return LexResponseService.build_fulfillment_response(
        intent_name=intent_name or "FallbackIntent",
        message=message,
        fulfilled=False,
    )
