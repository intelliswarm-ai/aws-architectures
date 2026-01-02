"""Unit tests for Pydantic models."""

import pytest
from datetime import datetime

from src.common.models import (
    Document,
    DocumentStatus,
    DocumentType,
    ExtractionResult,
    AnalysisResult,
    InferenceResult,
    GenerativeResult,
)


class TestDocument:
    """Tests for Document model."""

    def test_create_document(self):
        """Test creating a document with required fields."""
        doc = Document(
            document_id="test-123",
            bucket="my-bucket",
            key="input/test.pdf",
        )

        assert doc.document_id == "test-123"
        assert doc.bucket == "my-bucket"
        assert doc.key == "input/test.pdf"
        assert doc.document_type == DocumentType.UNKNOWN
        assert doc.status == DocumentStatus.PENDING

    def test_document_with_all_fields(self):
        """Test creating a document with all fields."""
        doc = Document(
            document_id="test-456",
            bucket="my-bucket",
            key="input/report.pdf",
            document_type=DocumentType.PDF,
            status=DocumentStatus.COMPLETED,
            file_size=1024,
            content_type="application/pdf",
            metadata={"source": "upload"},
        )

        assert doc.document_type == DocumentType.PDF
        assert doc.status == DocumentStatus.COMPLETED
        assert doc.file_size == 1024
        assert doc.metadata["source"] == "upload"


class TestExtractionResult:
    """Tests for ExtractionResult model."""

    def test_create_extraction_result(self):
        """Test creating an extraction result."""
        result = ExtractionResult(
            document_id="test-123",
            extracted_text="Hello World",
            confidence=0.95,
            words=2,
            pages=1,
        )

        assert result.document_id == "test-123"
        assert result.extracted_text == "Hello World"
        assert result.confidence == 0.95
        assert result.words == 2

    def test_extraction_result_with_tables(self):
        """Test extraction result with tables and forms."""
        result = ExtractionResult(
            document_id="test-123",
            extracted_text="Table data",
            tables=[{"rows": [["A", "B"], ["1", "2"]]}],
            forms=[{"key": "Name", "value": "John"}],
        )

        assert len(result.tables) == 1
        assert len(result.forms) == 1


class TestAnalysisResult:
    """Tests for AnalysisResult model."""

    def test_create_analysis_result(self):
        """Test creating an analysis result."""
        result = AnalysisResult(
            document_id="test-123",
            key_phrases=["machine learning", "AI"],
            language="en",
        )

        assert result.document_id == "test-123"
        assert len(result.key_phrases) == 2
        assert result.language == "en"


class TestInferenceResult:
    """Tests for InferenceResult model."""

    def test_create_inference_result(self):
        """Test creating an inference result."""
        result = InferenceResult(
            document_id="test-123",
            predicted_class="INVOICE",
            confidence=0.92,
            probabilities={"INVOICE": 0.92, "CONTRACT": 0.05, "OTHER": 0.03},
        )

        assert result.predicted_class == "INVOICE"
        assert result.confidence == 0.92
        assert result.probabilities["INVOICE"] == 0.92


class TestGenerativeResult:
    """Tests for GenerativeResult model."""

    def test_create_generative_result(self):
        """Test creating a generative result."""
        result = GenerativeResult(
            document_id="test-123",
            summary="This is a summary.",
            questions=[{"question": "What?", "answer": "Something"}],
            topics=["AI", "ML"],
        )

        assert result.summary == "This is a summary."
        assert len(result.questions) == 1
        assert len(result.topics) == 2
