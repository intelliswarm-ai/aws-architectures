"""Custom exceptions for AWS Lex airline chatbot."""


class LexBotError(Exception):
    """Base exception for Lex bot errors."""

    def __init__(self, message: str, error_code: str | None = None) -> None:
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)


class ValidationError(LexBotError):
    """Raised when slot validation fails."""

    def __init__(self, slot_name: str, message: str) -> None:
        self.slot_name = slot_name
        super().__init__(message, error_code="VALIDATION_ERROR")


class InvalidSlotError(LexBotError):
    """Raised when a slot value is invalid."""

    def __init__(self, slot_name: str, value: str, reason: str) -> None:
        self.slot_name = slot_name
        self.value = value
        self.reason = reason
        message = f"Invalid value '{value}' for slot '{slot_name}': {reason}"
        super().__init__(message, error_code="INVALID_SLOT")


class BookingError(LexBotError):
    """Raised when booking operation fails."""

    def __init__(self, message: str, booking_reference: str | None = None) -> None:
        self.booking_reference = booking_reference
        super().__init__(message, error_code="BOOKING_ERROR")


class BookingNotFoundError(BookingError):
    """Raised when booking is not found."""

    def __init__(self, booking_reference: str) -> None:
        message = f"Booking with reference '{booking_reference}' not found"
        super().__init__(message, booking_reference=booking_reference)
        self.error_code = "BOOKING_NOT_FOUND"


class FlightNotFoundError(LexBotError):
    """Raised when flight is not found."""

    def __init__(self, flight_id: str | None = None, search_criteria: str | None = None) -> None:
        self.flight_id = flight_id
        self.search_criteria = search_criteria
        if flight_id:
            message = f"Flight with ID '{flight_id}' not found"
        elif search_criteria:
            message = f"No flights found matching: {search_criteria}"
        else:
            message = "Flight not found"
        super().__init__(message, error_code="FLIGHT_NOT_FOUND")


class CheckInError(LexBotError):
    """Raised when check-in operation fails."""

    def __init__(
        self, message: str, booking_reference: str | None = None, reason: str | None = None
    ) -> None:
        self.booking_reference = booking_reference
        self.reason = reason
        super().__init__(message, error_code="CHECKIN_ERROR")


class CheckInWindowError(CheckInError):
    """Raised when check-in is attempted outside allowed window."""

    def __init__(self, booking_reference: str, hours_until_departure: int) -> None:
        self.hours_until_departure = hours_until_departure
        message = (
            f"Check-in for booking '{booking_reference}' is not available. "
            f"Check-in opens 24 hours before departure ({hours_until_departure} hours remaining)."
        )
        super().__init__(message, booking_reference=booking_reference, reason="OUTSIDE_WINDOW")
        self.error_code = "CHECKIN_WINDOW_ERROR"


class SeatUnavailableError(LexBotError):
    """Raised when requested seat is not available."""

    def __init__(self, seat_number: str, flight_number: str) -> None:
        self.seat_number = seat_number
        self.flight_number = flight_number
        message = f"Seat {seat_number} is not available on flight {flight_number}"
        super().__init__(message, error_code="SEAT_UNAVAILABLE")


class PaymentError(LexBotError):
    """Raised when payment processing fails."""

    def __init__(self, message: str, transaction_id: str | None = None) -> None:
        self.transaction_id = transaction_id
        super().__init__(message, error_code="PAYMENT_ERROR")
