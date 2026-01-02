################################################################################
# CloudWatch Monitoring Module
################################################################################

data "aws_region" "current" {}

################################################################################
# CloudWatch Dashboard
################################################################################

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # Kinesis Stream Metrics
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Kinesis Stream - Incoming Records"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Kinesis", "IncomingRecords", "StreamName", var.kinesis_stream_name, { stat = "Sum", period = 60 }]
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
          title  = "Kinesis Stream - Iterator Age"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Kinesis", "GetRecords.IteratorAgeMilliseconds", "StreamName", var.kinesis_stream_name, { stat = "Maximum", period = 60 }]
          ]
        }
      },
      # Lambda Invocations
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Invocations"
          region = data.aws_region.current.name
          metrics = [
            for name in var.lambda_function_names : ["AWS/Lambda", "Invocations", "FunctionName", name, { stat = "Sum", period = 60 }]
          ]
        }
      },
      # Lambda Errors
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Errors"
          region = data.aws_region.current.name
          metrics = [
            for name in var.lambda_function_names : ["AWS/Lambda", "Errors", "FunctionName", name, { stat = "Sum", period = 60 }]
          ]
        }
      },
      # Lambda Duration
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Duration (ms)"
          region = data.aws_region.current.name
          metrics = [
            for name in var.lambda_function_names : ["AWS/Lambda", "Duration", "FunctionName", name, { stat = "Average", period = 60 }]
          ]
        }
      },
      # Lambda Concurrent Executions
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Concurrent Executions"
          region = data.aws_region.current.name
          metrics = [
            for name in var.lambda_function_names : ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", name, { stat = "Maximum", period = 60 }]
          ]
        }
      },
      # Custom Metrics - GPS Tracking
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 8
        height = 6
        properties = {
          title  = "Coordinates Generated"
          region = data.aws_region.current.name
          metrics = [
            ["GPSTracking", "CoordinatesGenerated", { stat = "Sum", period = 60 }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 18
        width  = 8
        height = 6
        properties = {
          title  = "Positions Updated"
          region = data.aws_region.current.name
          metrics = [
            ["GPSTracking", "PositionsUpdated", { stat = "Sum", period = 60 }]
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 18
        width  = 8
        height = 6
        properties = {
          title  = "Geofence Alerts"
          region = data.aws_region.current.name
          metrics = [
            ["GPSTracking", "AlertsTriggered", { stat = "Sum", period = 60 }]
          ]
        }
      }
    ]
  })
}

################################################################################
# CloudWatch Alarms
################################################################################

# Lambda Error Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.key}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = var.error_threshold
  alarm_description   = "Lambda function ${each.key} is experiencing errors"

  dimensions = {
    FunctionName = each.key
  }

  tags = var.tags
}

# Lambda Duration Alarms
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.key}-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Average"
  threshold           = var.duration_threshold_ms
  alarm_description   = "Lambda function ${each.key} is running slowly"

  dimensions = {
    FunctionName = each.key
  }

  tags = var.tags
}
