"""Configuration settings for AWS Lex airline chatbot."""

import os
from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # AWS Configuration
    aws_region: str = Field(default="eu-central-2", alias="AWS_REGION")

    # DynamoDB Tables
    bookings_table: str = Field(default="airline-bookings", alias="BOOKINGS_TABLE")
    flights_table: str = Field(default="airline-flights", alias="FLIGHTS_TABLE")
    checkins_table: str = Field(default="airline-checkins", alias="CHECKINS_TABLE")

    # Logging
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Bot Configuration
    bot_id: str = Field(default="", alias="LEX_BOT_ID")
    bot_alias_id: str = Field(default="", alias="LEX_BOT_ALIAS_ID")

    # Business Rules
    max_passengers_per_booking: int = Field(default=9, alias="MAX_PASSENGERS")
    checkin_window_hours: int = Field(default=24, alias="CHECKIN_WINDOW_HOURS")
    booking_advance_days: int = Field(default=365, alias="BOOKING_ADVANCE_DAYS")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
