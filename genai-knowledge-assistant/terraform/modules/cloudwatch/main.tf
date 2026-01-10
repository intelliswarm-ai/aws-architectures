# =============================================================================
# CloudWatch Module - Monitoring & Alarms
# =============================================================================

# =============================================================================
# Dashboard
# =============================================================================

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # API Gateway Metrics
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "API Gateway - Requests"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiId", var.api_gateway_id, "Stage", var.api_gateway_stage, { label = "Requests" }]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "API Gateway - Latency"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/ApiGateway", "Latency", "ApiId", var.api_gateway_id, "Stage", var.api_gateway_stage, { label = "Latency (avg)" }],
            [".", "IntegrationLatency", ".", ".", ".", ".", { label = "Integration Latency" }]
          ]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "API Gateway - Errors"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/ApiGateway", "4XXError", "ApiId", var.api_gateway_id, "Stage", var.api_gateway_stage, { label = "4XX Errors", color = "#ff7f0e" }],
            [".", "5XXError", ".", ".", ".", ".", { label = "5XX Errors", color = "#d62728" }]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      # Lambda Metrics
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Lambda - Invocations"
          region = data.aws_region.current.name
          metrics = [for name in var.lambda_functions : ["AWS/Lambda", "Invocations", "FunctionName", name]]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Lambda - Duration"
          region = data.aws_region.current.name
          metrics = [for name in var.lambda_functions : ["AWS/Lambda", "Duration", "FunctionName", name]]
          period = 300
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Lambda - Errors"
          region = data.aws_region.current.name
          metrics = [for name in var.lambda_functions : ["AWS/Lambda", "Errors", "FunctionName", name]]
          period = 300
          stat   = "Sum"
        }
      },
      # Custom Metrics
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6
        properties = {
          title  = "GenAI - Queries & Tokens"
          region = data.aws_region.current.name
          metrics = [
            ["GenAIKnowledgeAssistant", "QueryCount", { label = "Queries" }],
            [".", "TokensUsed", { label = "Tokens", yAxis = "right" }]
          ]
          period = 300
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 18
        width  = 12
        height = 6
        properties = {
          title  = "GenAI - Documents"
          region = data.aws_region.current.name
          metrics = [
            ["GenAIKnowledgeAssistant", "DocumentsIngested", { label = "Ingested" }],
            [".", "DocumentsDeleted", { label = "Deleted" }]
          ]
          period = 300
          stat   = "Sum"
        }
      }
    ]
  })
}

# =============================================================================
# Alarms
# =============================================================================

# Lambda Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(var.lambda_functions)

  alarm_name          = "${var.project_prefix}-${each.key}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Lambda function ${each.key} error rate is high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = each.key
  }

  tags = var.tags
}

# API Gateway 5XX Errors
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "${var.project_prefix}-api-5xx-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5XXError"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "API Gateway 5XX error rate is high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = var.api_gateway_id
    Stage = var.api_gateway_stage
  }

  tags = var.tags
}

# API Gateway Latency
resource "aws_cloudwatch_metric_alarm" "api_latency" {
  alarm_name          = "${var.project_prefix}-api-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "Latency"
  namespace           = "AWS/ApiGateway"
  period              = 300
  statistic           = "Average"
  threshold           = 5000  # 5 seconds
  alarm_description   = "API Gateway latency is high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    ApiId = var.api_gateway_id
    Stage = var.api_gateway_stage
  }

  tags = var.tags
}

# =============================================================================
# Log Groups
# =============================================================================

resource "aws_cloudwatch_log_group" "application" {
  name              = "/aws/${var.project_prefix}/application"
  retention_in_days = var.environment == "prod" ? 90 : 30
  tags              = var.tags
}

# =============================================================================
# Data Sources
# =============================================================================

data "aws_region" "current" {}
