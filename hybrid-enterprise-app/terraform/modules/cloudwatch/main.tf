# ============================================
# CloudWatch Module - Monitoring & Alarms
# ============================================

# SNS Topic for Alarms
resource "aws_sns_topic" "alarms" {
  name = "${var.environment}-${var.application_name}-alarms"
}

resource "aws_sns_topic_subscription" "email" {
  count = var.alarm_email != "" ? 1 : 0

  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.environment}-${var.application_name}"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title   = "Environment Health"
          region  = data.aws_region.current.name
          metrics = [
            ["AWS/ElasticBeanstalk", "EnvironmentHealth", "EnvironmentName", var.eb_environment]
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
          title   = "Request Count"
          region  = data.aws_region.current.name
          metrics = [
            ["AWS/ElasticBeanstalk", "ApplicationRequestsTotal", "EnvironmentName", var.eb_environment]
          ]
          period = 60
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
          title   = "Response Latency"
          region  = data.aws_region.current.name
          metrics = [
            ["AWS/ElasticBeanstalk", "ApplicationLatencyP99", "EnvironmentName", var.eb_environment],
            ["AWS/ElasticBeanstalk", "ApplicationLatencyP90", "EnvironmentName", var.eb_environment],
            ["AWS/ElasticBeanstalk", "ApplicationLatencyP50", "EnvironmentName", var.eb_environment]
          ]
          period = 60
          stat   = "Average"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title   = "HTTP Error Rates"
          region  = data.aws_region.current.name
          metrics = [
            ["AWS/ElasticBeanstalk", "ApplicationRequests4xx", "EnvironmentName", var.eb_environment],
            ["AWS/ElasticBeanstalk", "ApplicationRequests5xx", "EnvironmentName", var.eb_environment]
          ]
          period = 60
          stat   = "Sum"
        }
      }
    ]
  })
}

# High Latency Alarm
resource "aws_cloudwatch_metric_alarm" "high_latency" {
  alarm_name          = "${var.environment}-${var.application_name}-high-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ApplicationLatencyP99"
  namespace           = "AWS/ElasticBeanstalk"
  period              = 60
  statistic           = "Average"
  threshold           = 5000  # 5 seconds
  alarm_description   = "Application latency is too high"

  dimensions = {
    EnvironmentName = var.eb_environment
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]
}

# High Error Rate Alarm
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "${var.environment}-${var.application_name}-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApplicationRequests5xx"
  namespace           = "AWS/ElasticBeanstalk"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "High 5xx error rate detected"

  dimensions = {
    EnvironmentName = var.eb_environment
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]
}

# Environment Health Alarm
resource "aws_cloudwatch_metric_alarm" "environment_health" {
  alarm_name          = "${var.environment}-${var.application_name}-environment-health"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "EnvironmentHealth"
  namespace           = "AWS/ElasticBeanstalk"
  period              = 60
  statistic           = "Average"
  threshold           = 15  # Warning or worse
  alarm_description   = "Environment health is degraded"

  dimensions = {
    EnvironmentName = var.eb_environment
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]
}

data "aws_region" "current" {}
