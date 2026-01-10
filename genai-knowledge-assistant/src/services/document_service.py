"""Document service for ingestion and management."""

import hashlib
import uuid
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer

from src.common.clients import get_dynamodb_resource, get_s3_client
from src.common.config import get_settings
from src.common.exceptions import (
    DocumentIngestionError,
    ResourceNotFoundError,
    ValidationError,
)
from src.common.models import (
    Document,
    DocumentChunk,
    DocumentMetadata,
    DocumentStatus,
    IngestionRequest,
    IngestionResponse,
    PaginatedResponse,
)
from src.services.embedding_service import EmbeddingService
from src.services.vector_store_service import VectorStoreService

logger = Logger()
tracer = Tracer()


class DocumentService:
    """Service for document ingestion and management."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.dynamodb = get_dynamodb_resource()
        self.s3 = get_s3_client()
        self.embedding_service = EmbeddingService()
        self.vector_store_service = VectorStoreService()

    @property
    def table(self):
        """Get DynamoDB table."""
        return self.dynamodb.Table(self.settings.documents_table)

    @tracer.capture_method
    def ingest(self, request: IngestionRequest) -> IngestionResponse:
        """
        Ingest a document into the knowledge base.

        Args:
            request: Ingestion request with source URI and metadata

        Returns:
            IngestionResponse with document ID and status
        """
        # Generate document ID
        document_id = self._generate_document_id(request.source_uri)

        logger.info(
            "Starting document ingestion",
            document_id=document_id,
            source_uri=request.source_uri,
        )

        try:
            # Create document record
            document = Document(
                document_id=document_id,
                knowledge_base_id=request.knowledge_base_id or self.settings.knowledge_base_id,
                source_type=request.source_type,
                source_uri=request.source_uri,
                status=DocumentStatus.PROCESSING,
                metadata=request.metadata or DocumentMetadata(),
            )

            # Save to DynamoDB
            self._save_document(document)

            if request.sync:
                # Synchronous processing
                self._process_document(document)
                document.status = DocumentStatus.INDEXED
                document.indexed_at = datetime.utcnow()
                self._save_document(document)

                return IngestionResponse(
                    document_id=document_id,
                    status=DocumentStatus.INDEXED,
                    message="Document indexed successfully",
                )

            # Async processing - just return pending status
            return IngestionResponse(
                document_id=document_id,
                status=DocumentStatus.PROCESSING,
                message="Document queued for processing",
            )

        except ValidationError:
            raise
        except Exception as e:
            logger.exception("Document ingestion failed")

            # Update document status to failed
            self._update_document_status(
                document_id=document_id,
                status=DocumentStatus.FAILED,
                error_message=str(e),
            )

            raise DocumentIngestionError(
                message=f"Ingestion failed: {str(e)}",
                document_id=document_id,
                source_uri=request.source_uri,
            )

    @tracer.capture_method
    def _process_document(self, document: Document) -> None:
        """Process document: extract text, chunk, embed, and index."""
        # Download content from S3
        content = self._download_document(document.source_uri)

        if not content:
            raise DocumentIngestionError(
                message="Empty document content",
                document_id=document.document_id,
                source_uri=document.source_uri,
            )

        # Chunk the content
        chunks = self._chunk_text(content, document.document_id)

        logger.info(
            "Document chunked",
            document_id=document.document_id,
            chunk_count=len(chunks),
        )

        # Generate embeddings
        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.generate_embeddings_batch(texts)

        # Prepare documents for indexing
        index_docs = []
        for chunk, embedding in zip(chunks, embeddings):
            index_docs.append({
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "content": chunk.content,
                "embedding": embedding,
                "metadata": {
                    "source_uri": document.source_uri,
                    "chunk_index": chunk.chunk_index,
                    **document.metadata.model_dump(by_alias=True),
                },
            })

        # Bulk index to vector store
        result = self.vector_store_service.bulk_index(index_docs)

        logger.info(
            "Document indexed",
            document_id=document.document_id,
            success_count=result["success_count"],
            failure_count=result["failure_count"],
        )

        if result["failure_count"] > 0:
            logger.warning(
                "Some chunks failed to index",
                errors=result["errors"],
            )

    @tracer.capture_method
    def _download_document(self, source_uri: str) -> str:
        """Download document content from S3."""
        if not source_uri.startswith("s3://"):
            raise ValidationError(
                message="Only S3 URIs are supported",
                field="source_uri",
                value=source_uri,
            )

        # Parse S3 URI
        parts = source_uri.replace("s3://", "").split("/", 1)
        bucket = parts[0]
        key = parts[1] if len(parts) > 1 else ""

        try:
            response = self.s3.get_object(Bucket=bucket, Key=key)
            content = response["Body"].read()

            # Determine content type and decode
            content_type = response.get("ContentType", "text/plain")

            if content_type.startswith("text/") or key.endswith((".txt", ".md", ".json")):
                return content.decode("utf-8")

            # For PDFs and other formats, would need additional processing
            # This is a simplified implementation
            logger.warning(
                "Non-text content type, attempting UTF-8 decode",
                content_type=content_type,
            )
            return content.decode("utf-8", errors="ignore")

        except self.s3.exceptions.NoSuchKey:
            raise ResourceNotFoundError(
                message=f"Document not found: {source_uri}",
                resource_type="S3Object",
                resource_id=source_uri,
            )
        except Exception as e:
            raise DocumentIngestionError(
                message=f"Failed to download document: {str(e)}",
                source_uri=source_uri,
            )

    def _chunk_text(
        self,
        text: str,
        document_id: str,
    ) -> list[DocumentChunk]:
        """Split text into chunks with overlap."""
        chunk_size = self.settings.chunk_size
        chunk_overlap = self.settings.chunk_overlap

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end within last 20% of chunk
                search_start = end - int(chunk_size * 0.2)
                for punct in [". ", ".\n", "? ", "?\n", "! ", "!\n"]:
                    pos = text.rfind(punct, search_start, end)
                    if pos > search_start:
                        end = pos + len(punct)
                        break

            chunk_content = text[start:end].strip()

            if chunk_content:
                chunk_id = f"{document_id}_{chunk_index:04d}"
                chunks.append(
                    DocumentChunk(
                        chunk_id=chunk_id,
                        document_id=document_id,
                        content=chunk_content,
                        chunk_index=chunk_index,
                        start_offset=start,
                        end_offset=end,
                    )
                )
                chunk_index += 1

            # Move to next chunk with overlap
            start = end - chunk_overlap
            if start >= len(text) - chunk_overlap:
                break

        return chunks

    def _generate_document_id(self, source_uri: str) -> str:
        """Generate deterministic document ID from source URI."""
        hash_input = source_uri.encode("utf-8")
        return hashlib.sha256(hash_input).hexdigest()[:16]

    @tracer.capture_method
    def _save_document(self, document: Document) -> None:
        """Save document to DynamoDB."""
        item = document.model_dump(by_alias=True)
        item["createdAt"] = item["createdAt"].isoformat()
        item["updatedAt"] = item["updatedAt"].isoformat()
        if item.get("indexedAt"):
            item["indexedAt"] = item["indexedAt"].isoformat()

        self.table.put_item(Item=item)

    @tracer.capture_method
    def _update_document_status(
        self,
        document_id: str,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> None:
        """Update document status in DynamoDB."""
        update_expr = "SET #status = :status, updatedAt = :updated"
        expr_values = {
            ":status": status.value,
            ":updated": datetime.utcnow().isoformat(),
        }
        expr_names = {"#status": "status"}

        if error_message:
            update_expr += ", errorMessage = :error"
            expr_values[":error"] = error_message

        if status == DocumentStatus.INDEXED:
            update_expr += ", indexedAt = :indexed"
            expr_values[":indexed"] = datetime.utcnow().isoformat()

        try:
            self.table.update_item(
                Key={"documentId": document_id},
                UpdateExpression=update_expr,
                ExpressionAttributeNames=expr_names,
                ExpressionAttributeValues=expr_values,
            )
        except Exception as e:
            logger.error("Failed to update document status", error=str(e))

    @tracer.capture_method
    def get_document(self, document_id: str) -> Document | None:
        """Get document by ID."""
        try:
            response = self.table.get_item(Key={"documentId": document_id})
            item = response.get("Item")

            if not item:
                return None

            return Document(**item)

        except Exception as e:
            logger.exception("Failed to get document")
            return None

    @tracer.capture_method
    def list_documents(
        self,
        page: int = 1,
        page_size: int = 20,
        status: str | None = None,
    ) -> PaginatedResponse[Document]:
        """List documents with pagination."""
        # This is a simplified scan - in production, use GSI
        scan_kwargs = {"Limit": page_size * page}

        if status:
            scan_kwargs["FilterExpression"] = "#status = :status"
            scan_kwargs["ExpressionAttributeNames"] = {"#status": "status"}
            scan_kwargs["ExpressionAttributeValues"] = {":status": status}

        try:
            response = self.table.scan(**scan_kwargs)
            items = response.get("Items", [])

            # Manual pagination (inefficient for large datasets)
            start_idx = (page - 1) * page_size
            page_items = items[start_idx:start_idx + page_size]

            documents = [Document(**item) for item in page_items]

            return PaginatedResponse(
                items=documents,
                total=response.get("Count", len(items)),
                page=page,
                page_size=page_size,
                has_more=len(items) > start_idx + page_size,
            )

        except Exception as e:
            logger.exception("Failed to list documents")
            return PaginatedResponse(items=[], total=0, page=page, page_size=page_size)

    @tracer.capture_method
    def delete_document(self, document_id: str) -> None:
        """Delete document and its chunks."""
        # Get document first
        document = self.get_document(document_id)
        if not document:
            raise ResourceNotFoundError(
                message=f"Document {document_id} not found",
                resource_type="Document",
                resource_id=document_id,
            )

        try:
            # Delete from vector store
            deleted_count = self.vector_store_service.delete_by_document_id(document_id)
            logger.info(
                "Deleted document chunks from vector store",
                document_id=document_id,
                deleted_count=deleted_count,
            )

            # Update status in DynamoDB
            self._update_document_status(document_id, DocumentStatus.DELETED)

        except Exception as e:
            logger.exception("Failed to delete document")
            raise DocumentIngestionError(
                message=f"Failed to delete document: {str(e)}",
                document_id=document_id,
            )
