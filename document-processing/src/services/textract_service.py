"""Textract service for document text extraction."""

import time
from typing import Any

from aws_lambda_powertools import Logger
from botocore.exceptions import ClientError

from src.common.clients import get_clients
from src.common.config import get_settings
from src.common.exceptions import ExtractionError, RetryableError
from src.common.models import ExtractionResult
from src.common.utils import clean_text

logger = Logger()


class TextractService:
    """Service for extracting text from documents using Amazon Textract."""

    def __init__(self):
        self.settings = get_settings()
        self.clients = get_clients()

    def extract_text_sync(
        self,
        bucket: str,
        key: str,
        document_id: str,
    ) -> ExtractionResult:
        """
        Extract text from a document synchronously.
        Best for small documents (< 5MB, < 3 pages).
        """
        try:
            response = self.clients.textract.detect_document_text(
                Document={"S3Object": {"Bucket": bucket, "Name": key}}
            )
            return self._parse_detect_response(document_id, response)

        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "")
            if error_code in ("ProvisionedThroughputExceededException", "ThrottlingException"):
                raise RetryableError(
                    f"Textract throttled: {e}",
                    document_id=document_id,
                    retry_after_seconds=30,
                )
            raise ExtractionError(
                f"Textract extraction failed: {e}",
                document_id=document_id,
                service="textract",
            )

    def extract_text_async(
        self,
        bucket: str,
        key: str,
        document_id: str,
        notification_topic_arn: str | None = None,
        notification_role_arn: str | None = None,
    ) -> str:
        """
        Start asynchronous text extraction.
        Returns job ID for status polling.
        Best for large documents (> 5MB or > 3 pages).
        """
        try:
            params: dict[str, Any] = {
                "DocumentLocation": {"S3Object": {"Bucket": bucket, "Name": key}},
                "ClientRequestToken": document_id[:64],
            }

            # Add notification channel if provided
            if notification_topic_arn and notification_role_arn:
                params["NotificationChannel"] = {
                    "SNSTopicArn": notification_topic_arn,
                    "RoleArn": notification_role_arn,
                }

            response = self.clients.textract.start_document_text_detection(**params)
            job_id = response["JobId"]

            logger.info(
                "Started async text extraction",
                document_id=document_id,
                job_id=job_id,
            )
            return job_id

        except ClientError as e:
            raise ExtractionError(
                f"Failed to start async extraction: {e}",
                document_id=document_id,
                service="textract",
            )

    def get_async_result(
        self,
        job_id: str,
        document_id: str,
        wait: bool = False,
        max_wait_seconds: int = 300,
    ) -> ExtractionResult | None:
        """
        Get result of async extraction job.
        Returns None if job is still in progress.
        """
        start_time = time.time()

        while True:
            try:
                response = self.clients.textract.get_document_text_detection(JobId=job_id)
                status = response["JobStatus"]

                if status == "SUCCEEDED":
                    return self._parse_async_response(document_id, job_id)
                elif status == "FAILED":
                    raise ExtractionError(
                        f"Textract job failed: {response.get('StatusMessage', 'Unknown error')}",
                        document_id=document_id,
                        service="textract",
                    )
                elif status == "IN_PROGRESS":
                    if not wait:
                        return None
                    if time.time() - start_time > max_wait_seconds:
                        raise ExtractionError(
                            f"Textract job timed out after {max_wait_seconds}s",
                            document_id=document_id,
                            service="textract",
                        )
                    time.sleep(5)  # Poll every 5 seconds

            except ClientError as e:
                raise ExtractionError(
                    f"Failed to get job status: {e}",
                    document_id=document_id,
                    service="textract",
                )

    def analyze_document(
        self,
        bucket: str,
        key: str,
        document_id: str,
        feature_types: list[str] | None = None,
    ) -> ExtractionResult:
        """
        Analyze document for tables and forms (sync).
        More expensive but extracts structured data.
        """
        if feature_types is None:
            feature_types = ["TABLES", "FORMS"]

        try:
            response = self.clients.textract.analyze_document(
                Document={"S3Object": {"Bucket": bucket, "Name": key}},
                FeatureTypes=feature_types,
            )
            return self._parse_analyze_response(document_id, response)

        except ClientError as e:
            raise ExtractionError(
                f"Textract analysis failed: {e}",
                document_id=document_id,
                service="textract",
            )

    def _parse_detect_response(
        self,
        document_id: str,
        response: dict[str, Any],
    ) -> ExtractionResult:
        """Parse DetectDocumentText response."""
        blocks = response.get("Blocks", [])
        lines = []
        total_confidence = 0.0
        word_count = 0

        for block in blocks:
            if block["BlockType"] == "LINE":
                lines.append(block.get("Text", ""))
                total_confidence += block.get("Confidence", 0)
            elif block["BlockType"] == "WORD":
                word_count += 1

        extracted_text = clean_text("\n".join(lines))
        avg_confidence = total_confidence / len(lines) if lines else 0

        return ExtractionResult(
            document_id=document_id,
            extracted_text=extracted_text,
            confidence=avg_confidence / 100,  # Convert to 0-1 range
            pages=response.get("DocumentMetadata", {}).get("Pages", 1),
            words=word_count,
            raw_response={"block_count": len(blocks)},
        )

    def _parse_async_response(
        self,
        document_id: str,
        job_id: str,
    ) -> ExtractionResult:
        """Parse async job results with pagination."""
        all_blocks: list[dict[str, Any]] = []
        next_token = None
        pages = 0

        while True:
            params: dict[str, Any] = {"JobId": job_id}
            if next_token:
                params["NextToken"] = next_token

            response = self.clients.textract.get_document_text_detection(**params)
            all_blocks.extend(response.get("Blocks", []))
            pages = response.get("DocumentMetadata", {}).get("Pages", pages)

            next_token = response.get("NextToken")
            if not next_token:
                break

        # Parse collected blocks
        lines = []
        total_confidence = 0.0
        word_count = 0

        for block in all_blocks:
            if block["BlockType"] == "LINE":
                lines.append(block.get("Text", ""))
                total_confidence += block.get("Confidence", 0)
            elif block["BlockType"] == "WORD":
                word_count += 1

        extracted_text = clean_text("\n".join(lines))
        avg_confidence = total_confidence / len(lines) if lines else 0

        return ExtractionResult(
            document_id=document_id,
            extracted_text=extracted_text,
            confidence=avg_confidence / 100,
            pages=pages,
            words=word_count,
            raw_response={"job_id": job_id, "block_count": len(all_blocks)},
        )

    def _parse_analyze_response(
        self,
        document_id: str,
        response: dict[str, Any],
    ) -> ExtractionResult:
        """Parse AnalyzeDocument response with tables and forms."""
        blocks = response.get("Blocks", [])
        lines = []
        tables: list[dict[str, Any]] = []
        forms: list[dict[str, Any]] = []
        word_count = 0
        total_confidence = 0.0

        # Build block map for relationships
        block_map = {block["Id"]: block for block in blocks}

        for block in blocks:
            block_type = block["BlockType"]

            if block_type == "LINE":
                lines.append(block.get("Text", ""))
                total_confidence += block.get("Confidence", 0)
            elif block_type == "WORD":
                word_count += 1
            elif block_type == "TABLE":
                table = self._extract_table(block, block_map)
                tables.append(table)
            elif block_type == "KEY_VALUE_SET":
                if "KEY" in block.get("EntityTypes", []):
                    form_field = self._extract_form_field(block, block_map)
                    if form_field:
                        forms.append(form_field)

        extracted_text = clean_text("\n".join(lines))
        avg_confidence = total_confidence / len(lines) if lines else 0

        return ExtractionResult(
            document_id=document_id,
            extracted_text=extracted_text,
            confidence=avg_confidence / 100,
            pages=response.get("DocumentMetadata", {}).get("Pages", 1),
            words=word_count,
            tables=tables,
            forms=forms,
            raw_response={"block_count": len(blocks)},
        )

    def _extract_table(
        self,
        table_block: dict[str, Any],
        block_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any]:
        """Extract table data from blocks."""
        rows: dict[int, dict[int, str]] = {}

        for relationship in table_block.get("Relationships", []):
            if relationship["Type"] == "CHILD":
                for cell_id in relationship["Ids"]:
                    cell = block_map.get(cell_id, {})
                    if cell.get("BlockType") == "CELL":
                        row_idx = cell.get("RowIndex", 0)
                        col_idx = cell.get("ColumnIndex", 0)
                        text = self._get_text_from_block(cell, block_map)
                        if row_idx not in rows:
                            rows[row_idx] = {}
                        rows[row_idx][col_idx] = text

        # Convert to list of lists
        table_data = []
        for row_idx in sorted(rows.keys()):
            row = rows[row_idx]
            row_data = [row.get(col_idx, "") for col_idx in sorted(row.keys())]
            table_data.append(row_data)

        return {"rows": table_data, "confidence": table_block.get("Confidence", 0)}

    def _extract_form_field(
        self,
        key_block: dict[str, Any],
        block_map: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        """Extract form key-value pair."""
        key_text = self._get_text_from_block(key_block, block_map)
        value_text = ""

        for relationship in key_block.get("Relationships", []):
            if relationship["Type"] == "VALUE":
                for value_id in relationship["Ids"]:
                    value_block = block_map.get(value_id, {})
                    value_text = self._get_text_from_block(value_block, block_map)

        if key_text:
            return {
                "key": key_text,
                "value": value_text,
                "confidence": key_block.get("Confidence", 0),
            }
        return None

    def _get_text_from_block(
        self,
        block: dict[str, Any],
        block_map: dict[str, dict[str, Any]],
    ) -> str:
        """Get text from a block by traversing child WORD blocks."""
        text_parts = []

        for relationship in block.get("Relationships", []):
            if relationship["Type"] == "CHILD":
                for child_id in relationship["Ids"]:
                    child = block_map.get(child_id, {})
                    if child.get("BlockType") == "WORD":
                        text_parts.append(child.get("Text", ""))

        return " ".join(text_parts)
