"""API Gateway handler for REST API endpoints."""

import json
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.event_handler.exceptions import (
    BadRequestError,
    NotFoundError,
    ServiceError,
)
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError as PydanticValidationError

from src.common.config import get_settings
from src.common.exceptions import (
    ResourceNotFoundError,
    ValidationError,
)
from src.common.models import (
    ApiResponse,
    IngestionRequest,
    QueryRequest,
)
from src.services.document_service import DocumentService
from src.services.knowledge_base_service import KnowledgeBaseService
from src.services.query_service import QueryService

logger = Logger()
tracer = Tracer()
metrics = Metrics()

app = APIGatewayRestResolver()
settings = get_settings()

# Initialize services
document_service = DocumentService()
query_service = QueryService()
knowledge_base_service = KnowledgeBaseService()


# =============================================================================
# Health Check
# =============================================================================


@app.get("/health")
@tracer.capture_method
def health_check() -> dict[str, Any]:
    """Health check endpoint."""
    return {"status": "healthy", "service": settings.powertools_service_name}


# =============================================================================
# Query Endpoints
# =============================================================================


@app.post("/query")
@tracer.capture_method
def query_knowledge_base() -> Response:
    """Query the knowledge base with RAG."""
    try:
        body = app.current_event.json_body
        request = QueryRequest(**body)

        logger.info("Processing query request", query_length=len(request.query))

        response = query_service.query(request)

        metrics.add_metric(name="QueryCount", unit="Count", value=1)
        metrics.add_metric(name="TokensUsed", unit="Count", value=response.tokens_used)

        return Response(
            status_code=200,
            content_type="application/json",
            body=json.dumps(
                ApiResponse(success=True, data=response.model_dump(by_alias=True)).model_dump(
                    by_alias=True
                )
            ),
        )

    except PydanticValidationError as e:
        raise BadRequestError(f"Invalid request: {e.errors()}")
    except ValidationError as e:
        raise BadRequestError(e.message)
    except ResourceNotFoundError as e:
        raise NotFoundError(e.message)
    except Exception as e:
        logger.exception("Query failed")
        raise ServiceError(f"Query failed: {str(e)}")


@app.post("/query/stream")
@tracer.capture_method
def query_knowledge_base_stream() -> Response:
    """Query the knowledge base with streaming response."""
    try:
        body = app.current_event.json_body
        request = QueryRequest(**body)

        logger.info("Processing streaming query", query_length=len(request.query))

        # For streaming, return a Lambda response URL or WebSocket connection info
        # This is a placeholder - actual streaming requires different architecture
        response = query_service.query(request)

        return Response(
            status_code=200,
            content_type="application/json",
            body=json.dumps(
                ApiResponse(success=True, data=response.model_dump(by_alias=True)).model_dump(
                    by_alias=True
                )
            ),
        )

    except Exception as e:
        logger.exception("Streaming query failed")
        raise ServiceError(f"Query failed: {str(e)}")


# =============================================================================
# Document Endpoints
# =============================================================================


@app.post("/documents")
@tracer.capture_method
def ingest_document() -> Response:
    """Ingest a new document into the knowledge base."""
    try:
        body = app.current_event.json_body
        request = IngestionRequest(**body)

        logger.info("Ingesting document", source_uri=request.source_uri)

        response = document_service.ingest(request)

        metrics.add_metric(name="DocumentsIngested", unit="Count", value=1)

        return Response(
            status_code=202,
            content_type="application/json",
            body=json.dumps(
                ApiResponse(success=True, data=response.model_dump(by_alias=True)).model_dump(
                    by_alias=True
                )
            ),
        )

    except PydanticValidationError as e:
        raise BadRequestError(f"Invalid request: {e.errors()}")
    except ValidationError as e:
        raise BadRequestError(e.message)
    except Exception as e:
        logger.exception("Document ingestion failed")
        raise ServiceError(f"Ingestion failed: {str(e)}")


@app.get("/documents/<document_id>")
@tracer.capture_method
def get_document(document_id: str) -> Response:
    """Get document details by ID."""
    try:
        document = document_service.get_document(document_id)

        if not document:
            raise NotFoundError(f"Document {document_id} not found")

        return Response(
            status_code=200,
            content_type="application/json",
            body=json.dumps(
                ApiResponse(success=True, data=document.model_dump(by_alias=True)).model_dump(
                    by_alias=True
                )
            ),
        )

    except NotFoundError:
        raise
    except Exception as e:
        logger.exception("Failed to get document")
        raise ServiceError(f"Failed to get document: {str(e)}")


@app.get("/documents")
@tracer.capture_method
def list_documents() -> Response:
    """List all documents in the knowledge base."""
    try:
        # Get query parameters
        params = app.current_event.query_string_parameters or {}
        page = int(params.get("page", 1))
        page_size = int(params.get("pageSize", 20))
        status = params.get("status")

        result = document_service.list_documents(
            page=page,
            page_size=page_size,
            status=status,
        )

        return Response(
            status_code=200,
            content_type="application/json",
            body=json.dumps(
                ApiResponse(success=True, data=result.model_dump(by_alias=True)).model_dump(
                    by_alias=True
                )
            ),
        )

    except Exception as e:
        logger.exception("Failed to list documents")
        raise ServiceError(f"Failed to list documents: {str(e)}")


@app.delete("/documents/<document_id>")
@tracer.capture_method
def delete_document(document_id: str) -> Response:
    """Delete a document from the knowledge base."""
    try:
        document_service.delete_document(document_id)

        metrics.add_metric(name="DocumentsDeleted", unit="Count", value=1)

        return Response(
            status_code=200,
            content_type="application/json",
            body=json.dumps(
                ApiResponse(success=True, data={"documentId": document_id, "deleted": True}).model_dump(
                    by_alias=True
                )
            ),
        )

    except ResourceNotFoundError as e:
        raise NotFoundError(e.message)
    except Exception as e:
        logger.exception("Failed to delete document")
        raise ServiceError(f"Failed to delete document: {str(e)}")


# =============================================================================
# Knowledge Base Endpoints
# =============================================================================


@app.get("/knowledge-bases")
@tracer.capture_method
def list_knowledge_bases() -> Response:
    """List available knowledge bases."""
    try:
        knowledge_bases = knowledge_base_service.list_knowledge_bases()

        return Response(
            status_code=200,
            content_type="application/json",
            body=json.dumps(
                ApiResponse(success=True, data=[kb.model_dump(by_alias=True) for kb in knowledge_bases]).model_dump(
                    by_alias=True
                )
            ),
        )

    except Exception as e:
        logger.exception("Failed to list knowledge bases")
        raise ServiceError(f"Failed to list knowledge bases: {str(e)}")


@app.post("/knowledge-bases/<knowledge_base_id>/sync")
@tracer.capture_method
def sync_knowledge_base(knowledge_base_id: str) -> Response:
    """Trigger synchronization of a knowledge base data source."""
    try:
        result = knowledge_base_service.start_ingestion_job(knowledge_base_id)

        return Response(
            status_code=202,
            content_type="application/json",
            body=json.dumps(
                ApiResponse(success=True, data=result).model_dump(by_alias=True)
            ),
        )

    except ResourceNotFoundError as e:
        raise NotFoundError(e.message)
    except Exception as e:
        logger.exception("Failed to sync knowledge base")
        raise ServiceError(f"Sync failed: {str(e)}")


# =============================================================================
# Lambda Handler
# =============================================================================


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Main Lambda handler for API Gateway events."""
    return app.resolve(event, context)
