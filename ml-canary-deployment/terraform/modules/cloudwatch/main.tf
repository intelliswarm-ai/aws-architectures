# CloudWatch Module - Monitoring, alarms, and scheduled events

# Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "Endpoint Invocations"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/SageMaker", "Invocations", "EndpointName", var.endpoint_name, "VariantName", "production"],
            ["...", "canary"]
          ]
          period = 60
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
          title  = "Model Latency (P99)"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/SageMaker", "ModelLatency", "EndpointName", var.endpoint_name, "VariantName", "production", { stat = "p99" }],
            ["...", "canary", { stat = "p99" }]
          ]
          period = 60
          annotations = {
            horizontal = [
              {
                value = var.latency_threshold_ms * 1000
                label = "Threshold"
                color = "#ff0000"
              }
            ]
          }
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "Error Rates"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/SageMaker", "Invocation4XXErrors", "EndpointName", var.endpoint_name, "VariantName", "production"],
            [".", "Invocation5XXErrors", ".", ".", ".", "."],
            [".", "Invocation4XXErrors", ".", ".", ".", "canary"],
            [".", "Invocation5XXErrors", ".", ".", ".", "."]
          ]
          period = 60
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
          title  = "Instance Utilization"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/SageMaker", "CPUUtilization", "EndpointName", var.endpoint_name, "VariantName", "production"],
            [".", "MemoryUtilization", ".", ".", ".", "."]
          ]
          period = 60
          stat   = "Average"
        }
      }
    ]
  })
}

# Latency Alarm
resource "aws_cloudwatch_metric_alarm" "latency_alarm" {
  alarm_name          = "${var.project_prefix}-latency-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ModelLatency"
  namespace           = "AWS/SageMaker"
  period              = 60
  statistic           = "p99"
  threshold           = var.latency_threshold_ms * 1000  # Convert to microseconds
  alarm_description   = "Model P99 latency exceeds threshold"

  dimensions = {
    EndpointName = var.endpoint_name
    VariantName  = "canary"
  }

  alarm_actions = [var.alerts_topic_arn]
  ok_actions    = [var.alerts_topic_arn]

  tags = var.tags
}

# Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "error_alarm" {
  alarm_name          = "${var.project_prefix}-error-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  threshold           = var.error_rate_threshold * 100  # Convert to percentage

  metric_query {
    id          = "error_rate"
    expression  = "(errors4xx + errors5xx) / invocations * 100"
    label       = "Error Rate"
    return_data = true
  }

  metric_query {
    id = "invocations"
    metric {
      metric_name = "Invocations"
      namespace   = "AWS/SageMaker"
      period      = 60
      stat        = "Sum"
      dimensions = {
        EndpointName = var.endpoint_name
        VariantName  = "canary"
      }
    }
  }

  metric_query {
    id = "errors4xx"
    metric {
      metric_name = "Invocation4XXErrors"
      namespace   = "AWS/SageMaker"
      period      = 60
      stat        = "Sum"
      dimensions = {
        EndpointName = var.endpoint_name
        VariantName  = "canary"
      }
    }
  }

  metric_query {
    id = "errors5xx"
    metric {
      metric_name = "Invocation5XXErrors"
      namespace   = "AWS/SageMaker"
      period      = 60
      stat        = "Sum"
      dimensions = {
        EndpointName = var.endpoint_name
        VariantName  = "canary"
      }
    }
  }

  alarm_description = "Canary variant error rate exceeds threshold"
  alarm_actions     = [var.alerts_topic_arn]
  ok_actions        = [var.alerts_topic_arn]

  tags = var.tags
}

# EventBridge rule for periodic monitoring
resource "aws_cloudwatch_event_rule" "monitoring_schedule" {
  name                = "${var.project_prefix}-monitoring-schedule"
  description         = "Trigger monitoring Lambda every minute"
  schedule_expression = "rate(1 minute)"

  tags = var.tags
}

resource "aws_cloudwatch_event_target" "monitoring" {
  rule      = aws_cloudwatch_event_rule.monitoring_schedule.name
  target_id = "MonitoringLambda"
  arn       = var.monitoring_lambda_arn
}

resource "aws_lambda_permission" "monitoring" {
  statement_id  = "AllowEventBridgeInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.monitoring_lambda_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monitoring_schedule.arn
}

data "aws_region" "current" {}
