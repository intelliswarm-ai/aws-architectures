"""Unit tests for Glue service."""

from unittest.mock import MagicMock, patch

import pytest

from src.common.exceptions import GlueJobError
from src.services.glue_service import GlueService


class TestGlueService:
    """Tests for GlueService."""

    @pytest.fixture
    def glue_service(self, mock_glue_client):
        """Create GlueService with mocked client."""
        with patch("src.services.glue_service.get_glue_client", return_value=mock_glue_client):
            service = GlueService()
            service._client = mock_glue_client
            return service

    def test_start_job_success(self, glue_service, mock_glue_client):
        """Test successful job start."""
        mock_glue_client.start_job_run.return_value = {"JobRunId": "jr_test_123"}

        run_id = glue_service.start_job(
            job_name="test-job",
            arguments={"--source_bucket": "test-bucket"},
        )

        assert run_id == "jr_test_123"
        mock_glue_client.start_job_run.assert_called_once()

    def test_start_job_failure(self, glue_service, mock_glue_client):
        """Test job start failure."""
        mock_glue_client.start_job_run.side_effect = Exception("Glue error")

        with pytest.raises(GlueJobError):
            glue_service.start_job(job_name="test-job")

    def test_get_job_run_success(self, glue_service, mock_glue_client):
        """Test getting job run details."""
        mock_glue_client.get_job_run.return_value = {
            "JobRun": {
                "Id": "jr_test_123",
                "JobName": "test-job",
                "State": "SUCCEEDED",
            }
        }

        result = glue_service.get_job_run("test-job", "jr_test_123")

        assert result["State"] == "SUCCEEDED"

    def test_get_job_runs(self, glue_service, mock_glue_client):
        """Test getting recent job runs."""
        mock_glue_client.get_job_runs.return_value = {
            "JobRuns": [
                {"Id": "jr_1", "State": "SUCCEEDED"},
                {"Id": "jr_2", "State": "FAILED"},
            ]
        }

        runs = glue_service.get_job_runs("test-job", max_results=10)

        assert len(runs) == 2

    def test_get_job_bookmark(self, glue_service, mock_glue_client):
        """Test getting job bookmark."""
        mock_glue_client.get_job_bookmark.return_value = {
            "JobBookmarkEntry": {
                "JobName": "test-job",
                "Version": 1,
            }
        }

        bookmark = glue_service.get_job_bookmark("test-job")

        assert bookmark["JobName"] == "test-job"

    def test_reset_job_bookmark(self, glue_service, mock_glue_client):
        """Test resetting job bookmark."""
        result = glue_service.reset_job_bookmark("test-job")

        assert result is True
        mock_glue_client.reset_job_bookmark.assert_called_once_with(JobName="test-job")

    def test_stop_job_run(self, glue_service, mock_glue_client):
        """Test stopping a job run."""
        result = glue_service.stop_job_run("test-job", "jr_test_123")

        assert result is True
        mock_glue_client.batch_stop_job_run.assert_called_once()

    def test_update_table_metadata(self, glue_service, mock_glue_client):
        """Test updating table metadata."""
        mock_glue_client.get_table.return_value = {
            "Table": {
                "Name": "test_table",
                "StorageDescriptor": {},
                "Parameters": {},
            }
        }

        result = glue_service.update_table_metadata(
            database_name="test_db",
            table_name="test_table",
            metadata={"lineage_id": "lr_123"},
        )

        assert result is True
        mock_glue_client.update_table.assert_called_once()
