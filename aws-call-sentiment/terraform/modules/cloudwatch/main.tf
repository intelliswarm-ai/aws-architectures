variable "environment" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "opensearch_domain_name" {
  type = string
}

variable "lambda_function_names" {
  type = list(string)
}

variable "alarm_email" {
  type    = string
  default = ""
}

# SNS Topic for alarms
resource "aws_sns_topic" "alarms" {
  name = "${var.name_prefix}-alarms"

  tags = {
    Name = "${var.name_prefix}-alarms"
  }
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alarm_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alarms.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# Dashboard
resource "aws_cloudwatch_dashboard" "main" {
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
            for fn in var.lambda_function_names : [
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
            for fn in var.lambda_function_names : [
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
            for fn in var.lambda_function_names : [
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
          title  = "OpenSearch Cluster Health"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/ES", "ClusterStatus.green", "DomainName", var.opensearch_domain_name, { stat = "Maximum" }],
            ["AWS/ES", "ClusterStatus.yellow", "DomainName", var.opensearch_domain_name, { stat = "Maximum" }],
            ["AWS/ES", "ClusterStatus.red", "DomainName", var.opensearch_domain_name, { stat = "Maximum" }]
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
          title  = "OpenSearch CPU & Memory"
          region = data.aws_region.current.name
          metrics = [
            ["AWS/ES", "CPUUtilization", "DomainName", var.opensearch_domain_name, { stat = "Average" }],
            ["AWS/ES", "JVMMemoryPressure", "DomainName", var.opensearch_domain_name, { stat = "Average" }]
          ]
        }
      }
    ]
  })
}

data "aws_region" "current" {}

# Lambda Error Alarm
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 300
  statistic           = "Sum"
  threshold           = 5

  dimensions = {
    FunctionName = each.value
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = {
    Name = "${each.value}-errors"
  }
}

# OpenSearch Cluster Red Alarm
resource "aws_cloudwatch_metric_alarm" "opensearch_red" {
  alarm_name          = "${var.name_prefix}-opensearch-red"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ClusterStatus.red"
  namespace           = "AWS/ES"
  period              = 60
  statistic           = "Maximum"
  threshold           = 0

  dimensions = {
    DomainName = var.opensearch_domain_name
  }

  alarm_actions = [aws_sns_topic.alarms.arn]
  ok_actions    = [aws_sns_topic.alarms.arn]

  tags = {
    Name = "${var.name_prefix}-opensearch-red"
  }
}

output "dashboard_url" {
  value = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "sns_topic_arn" {
  value = aws_sns_topic.alarms.arn
}
