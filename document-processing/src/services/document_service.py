"""Document management service for DynamoDB operations."""

from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger

from src.common.clients import get_clients, get_dynamodb_resource
from src.common.config import get_settings
from src.common.models import Document, DocumentStatus

logger = Logger()


class DocumentService:
    """Service for managing document state in DynamoDB."""

    def __init__(self):
        self.settings = get_settings()
        self.clients = get_clients()
        self.dynamodb = get_dynamodb_resource()
        self.table = self.dynamodb.Table(self.settings.documents_table)

    def create_document(self, document: Document) -> Document:
        """Create a new document record."""
        item = self._document_to_item(document)
        self.table.put_item(Item=item)
        logger.info("Created document record", document_id=document.document_id)
        return document

    def get_document(self, document_id: str) -> Document | None:
        """Get document by ID."""
        response = self.table.get_item(Key={"document_id": document_id})
        item = response.get("Item")
        if not item:
            return None
        return self._item_to_document(item)

    def update_status(
        self,
        document_id: str,
        status: DocumentStatus,
        error_message: str | None = None,
    ) -> Document | None:
        """Update document status."""
        update_expression = "SET #status = :status, updated_at = :updated_at"
        expression_values: dict[str, Any] = {
            ":status": status.value,
            ":updated_at": datetime.utcnow().isoformat(),
        }
        expression_names = {"#status": "status"}

        if error_message:
            update_expression += ", error_message = :error_message"
            expression_values[":error_message"] = error_message

        response = self.table.update_item(
            Key={"document_id": document_id},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ReturnValues="ALL_NEW",
        )
        item = response.get("Attributes")
        if not item:
            return None

        logger.info("Updated document status", document_id=document_id, status=status.value)
        return self._item_to_document(item)

    def update_metadata(
        self,
        document_id: str,
        metadata: dict[str, Any],
    ) -> Document | None:
        """Update document metadata."""
        response = self.table.update_item(
            Key={"document_id": document_id},
            UpdateExpression="SET metadata = :metadata, updated_at = :updated_at",
            ExpressionAttributeValues={
                ":metadata": metadata,
                ":updated_at": datetime.utcnow().isoformat(),
            },
            ReturnValues="ALL_NEW",
        )
        item = response.get("Attributes")
        return self._item_to_document(item) if item else None

    def increment_retry_count(self, document_id: str) -> int:
        """Increment retry count and return new value."""
        response = self.table.update_item(
            Key={"document_id": document_id},
            UpdateExpression="SET retry_count = if_not_exists(retry_count, :zero) + :inc",
            ExpressionAttributeValues={":zero": 0, ":inc": 1},
            ReturnValues="UPDATED_NEW",
        )
        return response.get("Attributes", {}).get("retry_count", 1)

    def save_processing_result(
        self,
        document_id: str,
        result_type: str,
        result: dict[str, Any],
    ) -> None:
        """Save processing result to document metadata."""
        self.table.update_item(
            Key={"document_id": document_id},
            UpdateExpression="SET metadata.#result_type = :result, updated_at = :updated_at",
            ExpressionAttributeNames={"#result_type": result_type},
            ExpressionAttributeValues={
                ":result": result,
                ":updated_at": datetime.utcnow().isoformat(),
            },
        )
        logger.info(
            "Saved processing result",
            document_id=document_id,
            result_type=result_type,
        )

    def list_documents_by_status(
        self,
        status: DocumentStatus,
        limit: int = 100,
    ) -> list[Document]:
        """List documents by status using GSI."""
        response = self.table.query(
            IndexName="status-index",
            KeyConditionExpression="status = :status",
            ExpressionAttributeValues={":status": status.value},
            Limit=limit,
        )
        return [self._item_to_document(item) for item in response.get("Items", [])]

    def _document_to_item(self, document: Document) -> dict[str, Any]:
        """Convert Document model to DynamoDB item."""
        return {
            "document_id": document.document_id,
            "bucket": document.bucket,
            "key": document.key,
            "document_type": document.document_type.value if hasattr(document.document_type, "value") else document.document_type,
            "status": document.status.value if hasattr(document.status, "value") else document.status,
            "file_size": document.file_size,
            "content_type": document.content_type,
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "metadata": document.metadata,
            "error_message": document.error_message,
            "retry_count": document.retry_count,
        }

    def _item_to_document(self, item: dict[str, Any]) -> Document:
        """Convert DynamoDB item to Document model."""
        return Document(
            document_id=item["document_id"],
            bucket=item["bucket"],
            key=item["key"],
            document_type=item.get("document_type", "UNKNOWN"),
            status=item.get("status", "PENDING"),
            file_size=item.get("file_size"),
            content_type=item.get("content_type"),
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            metadata=item.get("metadata", {}),
            error_message=item.get("error_message"),
            retry_count=item.get("retry_count", 0),
        )
