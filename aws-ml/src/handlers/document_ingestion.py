"""Document ingestion handler - triggered by S3 events."""

import json
from datetime import datetime
from typing import Any

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.models import Document, DocumentStatus, WorkflowInput
from src.common.utils import (
    detect_document_type,
    generate_document_id,
    get_content_type,
    parse_s3_event,
)
from src.services.document_service import DocumentService

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handle S3 event for document ingestion.

    Triggered when a document is uploaded to the raw documents bucket.
    Creates a document record in DynamoDB and starts the processing workflow.
    """
    settings = get_settings()
    clients = get_clients()
    doc_service = DocumentService()

    # Parse S3 event
    records = parse_s3_event(event)
    logger.info("Processing S3 events", record_count=len(records))

    results = []

    for record in records:
        bucket = record["bucket"]
        key = record["key"]

        try:
            # Skip if not in input folder
            if not key.startswith("input/"):
                logger.info("Skipping non-input file", key=key)
                continue

            # Get object metadata
            head_response = clients.s3.head_object(Bucket=bucket, Key=key)
            file_size = head_response.get("ContentLength", 0)
            content_type = head_response.get("ContentType") or get_content_type(key)

            # Detect document type
            doc_type = detect_document_type(key, content_type)

            # Create document record
            document_id = generate_document_id()
            document = Document(
                document_id=document_id,
                bucket=bucket,
                key=key,
                document_type=doc_type,
                status=DocumentStatus.INGESTED,
                file_size=file_size,
                content_type=content_type,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            # Save to DynamoDB
            doc_service.create_document(document)

            logger.info(
                "Document ingested",
                document_id=document_id,
                document_type=doc_type.value,
                file_size=file_size,
            )

            # Start Step Functions workflow
            workflow_input = WorkflowInput(
                document_id=document_id,
                bucket=bucket,
                key=key,
                document_type=doc_type,
            )

            execution_response = clients.sfn.start_execution(
                stateMachineArn=settings.workflow_arn,
                name=f"doc-{document_id}",
                input=json.dumps(workflow_input.model_dump()),
            )

            execution_arn = execution_response["executionArn"]

            logger.info(
                "Started workflow",
                document_id=document_id,
                execution_arn=execution_arn,
            )

            results.append(
                {
                    "document_id": document_id,
                    "status": "ingested",
                    "execution_arn": execution_arn,
                }
            )

        except Exception as e:
            logger.exception("Failed to ingest document", bucket=bucket, key=key)
            results.append(
                {
                    "bucket": bucket,
                    "key": key,
                    "status": "failed",
                    "error": str(e),
                }
            )

    return {
        "statusCode": 200,
        "body": {"processed": len(results), "results": results},
    }
