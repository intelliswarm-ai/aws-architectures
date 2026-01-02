# ---------------------------------------------------------------------------------------------------------------------
# CLOUDWATCH MONITORING AND LOGGING
# ---------------------------------------------------------------------------------------------------------------------

# Log groups for Lambda functions
resource "aws_cloudwatch_log_group" "lambda" {
  for_each = toset(var.lambda_functions)

  name              = "/aws/lambda/${each.value}"
  retention_in_days = var.log_retention_days
}

# Log group for Glue ETL job
resource "aws_cloudwatch_log_group" "glue" {
  name              = "/aws-glue/jobs/${var.glue_job_name}"
  retention_in_days = var.log_retention_days
}

# Dashboard for data lake monitoring
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-${var.environment}-datalake"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Invocations"
          region = data.aws_region.current.name
          metrics = [
            for fn in var.lambda_functions : [
              "AWS/Lambda", "Invocations",
              "FunctionName", fn,
              { stat = "Sum", period = 300 }
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Errors"
          region = data.aws_region.current.name
          metrics = [
            for fn in var.lambda_functions : [
              "AWS/Lambda", "Errors",
              "FunctionName", fn,
              { stat = "Sum", period = 300 }
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Duration"
          region = data.aws_region.current.name
          metrics = [
            for fn in var.lambda_functions : [
              "AWS/Lambda", "Duration",
              "FunctionName", fn,
              { stat = "Average", period = 300 }
            ]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Athena Query Execution"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Athena", "TotalExecutionTime", "WorkGroup", var.athena_workgroup, { stat = "Average" }],
            ["AWS/Athena", "QueryQueueTime", "WorkGroup", var.athena_workgroup, { stat = "Average" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Athena Data Scanned"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Athena", "ProcessedBytes", "WorkGroup", var.athena_workgroup, { stat = "Sum" }],
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Glue Job Metrics"
          region = data.aws_region.current.name
          metrics = [
            ["Glue", "glue.driver.aggregate.numCompletedTasks", "JobName", var.glue_job_name, "JobRunId", "ALL", { stat = "Sum" }],
            ["Glue", "glue.driver.aggregate.numFailedTasks", "JobName", var.glue_job_name, "JobRunId", "ALL", { stat = "Sum" }],
          ]
        }
      }
    ]
  })
}

data "aws_region" "current" {}

# Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(var.lambda_functions)

  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "Lambda function ${each.value} errors exceeded threshold"

  dimensions = {
    FunctionName = each.value
  }

  alarm_actions = var.alarm_actions
  ok_actions    = var.ok_actions
}

# Alarm for Athena query costs
resource "aws_cloudwatch_metric_alarm" "athena_data_scanned" {
  alarm_name          = "${var.project_name}-${var.environment}-athena-data-scanned"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ProcessedBytes"
  namespace           = "AWS/Athena"
  period              = 3600
  statistic           = "Sum"
  threshold           = var.athena_bytes_threshold
  alarm_description   = "Athena data scanned exceeded threshold (cost control)"

  dimensions = {
    WorkGroup = var.athena_workgroup
  }

  alarm_actions = var.alarm_actions
}

# Alarm for Glue job failures
resource "aws_cloudwatch_metric_alarm" "glue_failures" {
  alarm_name          = "${var.project_name}-${var.environment}-glue-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "Glue"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Glue ETL job has failed tasks"

  dimensions = {
    JobName  = var.glue_job_name
    JobRunId = "ALL"
  }

  alarm_actions = var.alarm_actions
}
