variable "name_prefix" {
  type = string
}

variable "environment" {
  type = string
}

variable "fulfillment_lambda_name" {
  type = string
}

variable "lex_bot_id" {
  type = string
}

data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "airline_chatbot" {
  dashboard_name = "${var.name_prefix}-dashboard"

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
            ["AWS/Lambda", "Invocations", "FunctionName", var.fulfillment_lambda_name, { stat = "Sum", period = 300 }],
            ["AWS/Lambda", "Errors", "FunctionName", var.fulfillment_lambda_name, { stat = "Sum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Duration"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Lambda", "Duration", "FunctionName", var.fulfillment_lambda_name, { stat = "Average", period = 300 }],
            ["AWS/Lambda", "Duration", "FunctionName", var.fulfillment_lambda_name, { stat = "Maximum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Lex Bot Metrics"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Lex", "MissedUtteranceCount", "BotId", var.lex_bot_id, { stat = "Sum", period = 300 }],
            ["AWS/Lex", "RuntimeRequestCount", "BotId", var.lex_bot_id, { stat = "Sum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Concurrent Executions"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", var.fulfillment_lambda_name, { stat = "Maximum", period = 300 }]
          ]
          view = "timeSeries"
        }
      },
      {
        type   = "log"
        x      = 0
        y      = 12
        width  = 24
        height = 6
        properties = {
          title  = "Recent Errors"
          region = data.aws_region.current.name
          query  = "SOURCE '/aws/lambda/${var.fulfillment_lambda_name}' | fields @timestamp, @message | filter @message like /ERROR/ | sort @timestamp desc | limit 50"
          view   = "table"
        }
      }
    ]
  })
}

# Alarm for Lambda errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.name_prefix}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda function errors exceeded threshold"

  dimensions = {
    FunctionName = var.fulfillment_lambda_name
  }

  treat_missing_data = "notBreaching"
}

# Alarm for missed utterances
resource "aws_cloudwatch_metric_alarm" "missed_utterances" {
  alarm_name          = "${var.name_prefix}-missed-utterances"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "MissedUtteranceCount"
  namespace           = "AWS/Lex"
  period              = 300
  statistic           = "Sum"
  threshold           = 20
  alarm_description   = "High number of missed utterances - consider adding more training phrases"

  dimensions = {
    BotId = var.lex_bot_id
  }

  treat_missing_data = "notBreaching"
}

# Alarm for Lambda duration
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.name_prefix}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Average"
  threshold           = 25000  # 25 seconds
  alarm_description   = "Lambda duration approaching timeout"

  dimensions = {
    FunctionName = var.fulfillment_lambda_name
  }

  treat_missing_data = "notBreaching"
}

output "dashboard_url" {
  value = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.airline_chatbot.dashboard_name}"
}
