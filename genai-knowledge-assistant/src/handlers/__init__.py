"""Lambda handlers for the GenAI Knowledge Assistant."""

from src.handlers.agent_handler import handler as agent_handler
from src.handlers.api_handler import handler as api_handler
from src.handlers.ingestion_handler import handler as ingestion_handler
from src.handlers.query_handler import handler as query_handler
from src.handlers.sync_handler import handler as sync_handler

__all__ = [
    "api_handler",
    "query_handler",
    "ingestion_handler",
    "agent_handler",
    "sync_handler",
]
