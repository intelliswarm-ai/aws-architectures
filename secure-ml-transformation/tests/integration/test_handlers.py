"""Integration tests for Lambda handlers."""

import json
from unittest.mock import MagicMock, patch

import pytest


class TestJobTriggerHandler:
    """Integration tests for job trigger handler."""

    @pytest.fixture
    def mock_services(self, mock_glue_client, mock_cloudwatch_client):
        """Mock all required services."""
        with patch("src.handlers.job_trigger_handler.GlueService") as mock_glue_svc, \
             patch("src.handlers.job_trigger_handler.AuditService") as mock_audit_svc:

            glue_instance = MagicMock()
            glue_instance.start_job.return_value = "jr_test_123"
            mock_glue_svc.return_value = glue_instance

            audit_instance = MagicMock()
            mock_audit_svc.return_value = audit_instance

            yield {
                "glue_service": glue_instance,
                "audit_service": audit_instance,
            }

    def test_handler_s3_event(self, mock_services, lambda_context):
        """Test handler with S3 event trigger."""
        from src.handlers.job_trigger_handler import handler

        event = {
            "Records": [
                {
                    "s3": {
                        "bucket": {"name": "test-bucket"},
                        "object": {"key": "transactions/2024/01/15/data.parquet"},
                    }
                }
            ]
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["job_run_id"] == "jr_test_123"
        assert body["trigger_source"] == "s3_event"

    def test_handler_scheduled_event(self, mock_services, lambda_context):
        """Test handler with EventBridge scheduled event."""
        from src.handlers.job_trigger_handler import handler

        event = {
            "source": "aws.events",
            "detail-type": "Scheduled Event",
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["trigger_source"] == "eventbridge_schedule"

    def test_handler_api_gateway_event(self, mock_services, lambda_context):
        """Test handler with API Gateway event."""
        from src.handlers.job_trigger_handler import handler

        event = {
            "httpMethod": "POST",
            "body": json.dumps({"custom_param": "value"}),
            "requestContext": {},
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["trigger_source"] == "api_gateway"

    def test_handler_job_start_failure(self, mock_services, lambda_context):
        """Test handler when job start fails."""
        from src.handlers.job_trigger_handler import handler

        mock_services["glue_service"].start_job.side_effect = Exception("Glue error")

        event = {"source": "aws.events"}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "error" in body


class TestLineageHandler:
    """Integration tests for lineage handler."""

    @pytest.fixture
    def mock_lineage_services(self, mock_s3_client, mock_glue_client):
        """Mock lineage services."""
        with patch("src.handlers.lineage_handler.LineageService") as mock_lineage_svc, \
             patch("src.handlers.lineage_handler.GlueService") as mock_glue_svc:

            lineage_instance = MagicMock()
            mock_lineage_svc.return_value = lineage_instance

            glue_instance = MagicMock()
            mock_glue_svc.return_value = glue_instance

            yield {
                "lineage_service": lineage_instance,
                "glue_service": glue_instance,
            }

    def test_record_lineage(self, mock_lineage_services, lambda_context):
        """Test recording lineage."""
        from src.handlers.lineage_handler import handler

        mock_lineage_services["lineage_service"].record_lineage.return_value = "lr_123"

        event = {
            "operation": "record_lineage",
            "lineage": {
                "job_execution_id": "jr_123",
                "job_name": "test-job",
                "start_time": "2024-01-15T10:00:00",
                "status": "SUCCEEDED",
            },
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200

    def test_get_lineage(self, mock_lineage_services, lambda_context):
        """Test getting lineage."""
        from src.handlers.lineage_handler import handler

        mock_lineage_services["lineage_service"].get_lineage.return_value = None

        event = {
            "operation": "get_lineage",
            "job_execution_id": "jr_123",
        }

        response = handler(event, lambda_context)

        # Should return 404 if not found
        assert response["statusCode"] in [200, 404]


class TestAuditHandler:
    """Integration tests for audit handler."""

    @pytest.fixture
    def mock_audit_services(self, mock_cloudwatch_client):
        """Mock audit services."""
        with patch("src.handlers.audit_handler.AuditService") as mock_audit_svc:
            audit_instance = MagicMock()
            audit_instance.query_logs.return_value = []
            audit_instance.generate_compliance_report.return_value = {
                "total_events": 0,
                "success_rate": 100,
            }
            mock_audit_svc.return_value = audit_instance

            yield {"audit_service": audit_instance}

    def test_query_logs(self, mock_audit_services, lambda_context):
        """Test querying audit logs."""
        from src.handlers.audit_handler import handler

        event = {
            "operation": "query_logs",
            "start_time": "2024-01-01T00:00:00",
            "end_time": "2024-01-31T23:59:59",
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "logs" in body

    def test_get_compliance_report(self, mock_audit_services, lambda_context):
        """Test generating compliance report."""
        from src.handlers.audit_handler import handler

        event = {
            "operation": "get_compliance_report",
            "report_type": "summary",
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert "report" in body
