################################################################################
# CloudWatch Resources for Monitoring and Audit Logging
################################################################################

data "aws_region" "current" {}

################################################################################
# Log Groups
################################################################################

resource "aws_cloudwatch_log_group" "audit" {
  name              = "/aws/glue/${var.name_prefix}/audit"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = {
    Name    = "${var.name_prefix}-audit-logs"
    Purpose = "Audit"
  }
}

resource "aws_cloudwatch_log_group" "etl" {
  name              = "/aws/glue/${var.name_prefix}/etl"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = {
    Name = "${var.name_prefix}-etl-logs"
  }
}

resource "aws_cloudwatch_log_group" "databrew" {
  name              = "/aws/databrew/${var.name_prefix}"
  retention_in_days = var.log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = {
    Name = "${var.name_prefix}-databrew-logs"
  }
}

################################################################################
# Metric Filters
################################################################################

resource "aws_cloudwatch_log_metric_filter" "job_failures" {
  name           = "${var.name_prefix}-job-failures"
  pattern        = "{ $.event_type = \"JOB_FAILED\" }"
  log_group_name = aws_cloudwatch_log_group.etl.name

  metric_transformation {
    name          = "GlueJobFailures"
    namespace     = "${var.project_name}/${var.environment}"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "pii_tokenization" {
  name           = "${var.name_prefix}-pii-tokenization"
  pattern        = "{ $.event_type = \"PII_TOKENIZATION\" }"
  log_group_name = aws_cloudwatch_log_group.audit.name

  metric_transformation {
    name          = "PIITokenizationEvents"
    namespace     = "${var.project_name}/${var.environment}"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_log_metric_filter" "anomaly_detection" {
  name           = "${var.name_prefix}-anomaly-detection"
  pattern        = "{ $.event_type = \"ANOMALY_DETECTED\" }"
  log_group_name = aws_cloudwatch_log_group.audit.name

  metric_transformation {
    name          = "AnomaliesDetected"
    namespace     = "${var.project_name}/${var.environment}"
    value         = "$.details.anomaly_count"
    default_value = "0"
  }
}

################################################################################
# Alarms
################################################################################

resource "aws_cloudwatch_metric_alarm" "job_failures" {
  alarm_name          = "${var.name_prefix}-job-failures"
  alarm_description   = "Alert on Glue job failures"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "GlueJobFailures"
  namespace           = "${var.project_name}/${var.environment}"
  period              = 300
  statistic           = "Sum"
  threshold           = 1
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${var.name_prefix}-job-failures-alarm"
  }
}

resource "aws_cloudwatch_metric_alarm" "high_anomaly_rate" {
  alarm_name          = "${var.name_prefix}-high-anomaly-rate"
  alarm_description   = "Alert on unusually high anomaly detection rate"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = 1
  metric_name         = "AnomaliesDetected"
  namespace           = "${var.project_name}/${var.environment}"
  period              = 3600
  statistic           = "Sum"
  threshold           = 1000
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${var.name_prefix}-high-anomaly-rate-alarm"
  }
}

################################################################################
# Dashboard
################################################################################

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = var.name_prefix

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Glue Job Metrics"
          region = data.aws_region.current.name
          metrics = [
            ["Glue", "glue.driver.aggregate.numCompletedTasks", "JobName", "${var.name_prefix}-main-etl", "Type", "gauge"],
            [".", "glue.driver.aggregate.numFailedTasks", ".", ".", ".", "."]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Job Failures"
          region = data.aws_region.current.name
          metrics = [
            ["${var.project_name}/${var.environment}", "GlueJobFailures"]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "PII Tokenization Events"
          region = data.aws_region.current.name
          metrics = [
            ["${var.project_name}/${var.environment}", "PIITokenizationEvents"]
          ]
          period = 3600
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Anomalies Detected"
          region = data.aws_region.current.name
          metrics = [
            ["${var.project_name}/${var.environment}", "AnomaliesDetected"]
          ]
          period = 3600
          stat   = "Sum"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6
        properties = {
          title  = "Recent Audit Events"
          region = data.aws_region.current.name
          query  = "SOURCE '/aws/glue/${var.name_prefix}/audit' | fields @timestamp, event_type, job_execution_id, details.records_processed | sort @timestamp desc | limit 20"
        }
      }
    ]
  })
}
