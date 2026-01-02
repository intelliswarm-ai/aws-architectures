################################################################################
# CloudWatch Module - Monitoring and Alerting
################################################################################

# Log Group for EC2 Instances
resource "aws_cloudwatch_log_group" "processor" {
  name              = "/banking/${var.project_name}/processor"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Log Group for Lambda Functions
resource "aws_cloudwatch_log_group" "lambda" {
  for_each = toset(var.lambda_function_names)

  name              = "/aws/lambda/${each.value}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.project_name}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6
        properties = {
          title  = "SQS Queue Depth"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.sqs_queue_name],
            [".", "ApproximateNumberOfMessagesNotVisible", ".", "."],
            [".", "ApproximateNumberOfMessagesDelayed", ".", "."]
          ]
          period = 60
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
          title  = "Auto Scaling Group Capacity"
          region = var.aws_region
          metrics = [
            ["AWS/AutoScaling", "GroupInServiceInstances", "AutoScalingGroupName", var.asg_name],
            [".", "GroupDesiredCapacity", ".", "."],
            [".", "GroupMinSize", ".", "."],
            [".", "GroupMaxSize", ".", "."]
          ]
          period = 60
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
          title  = "Messages Per Instance (Custom Metric)"
          region = var.aws_region
          metrics = [
            ["BankingPlatform/SQS", "BacklogPerInstance", "QueueName", "transaction-queue", "AutoScalingGroupName", var.asg_name]
          ]
          period = 60
          stat   = "Average"
          annotations = {
            horizontal = [
              {
                value = var.target_messages_per_instance
                label = "Target"
                color = "#ff7f0e"
              }
            ]
          }
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 6
        width  = 12
        height = 6
        properties = {
          title  = "SQS Age of Oldest Message"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateAgeOfOldestMessage", "QueueName", var.sqs_queue_name]
          ]
          period = 60
          stat   = "Maximum"
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Dead Letter Queue Depth"
          region = var.aws_region
          metrics = [
            ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.dlq_name]
          ]
          period = 60
          stat   = "Sum"
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 12
        width  = 12
        height = 6
        properties = {
          title  = "Lambda Invocations and Errors"
          region = var.aws_region
          metrics = concat(
            [for name in var.lambda_function_names : ["AWS/Lambda", "Invocations", "FunctionName", name]],
            [for name in var.lambda_function_names : [".", "Errors", ".", name]]
          )
          period = 60
          stat   = "Sum"
        }
      }
    ]
  })
}

# Alarm: High Queue Depth
resource "aws_cloudwatch_metric_alarm" "high_queue_depth" {
  alarm_name          = "${var.project_name}-high-queue-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Average"
  threshold           = var.queue_depth_threshold
  alarm_description   = "Queue depth exceeds ${var.queue_depth_threshold} messages"

  dimensions = {
    QueueName = var.sqs_queue_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []
  ok_actions    = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm: Old Messages in Queue
resource "aws_cloudwatch_metric_alarm" "old_messages" {
  alarm_name          = "${var.project_name}-old-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ApproximateAgeOfOldestMessage"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Maximum"
  threshold           = var.message_age_threshold_seconds
  alarm_description   = "Oldest message age exceeds ${var.message_age_threshold_seconds} seconds"

  dimensions = {
    QueueName = var.sqs_queue_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm: DLQ Has Messages
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.project_name}-dlq-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Sum"
  threshold           = var.dlq_message_threshold
  alarm_description   = "Dead letter queue has ${var.dlq_message_threshold}+ messages"

  dimensions = {
    QueueName = var.dlq_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm: ASG Below Minimum
resource "aws_cloudwatch_metric_alarm" "asg_below_minimum" {
  alarm_name          = "${var.project_name}-asg-below-minimum"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 2
  metric_name         = "GroupInServiceInstances"
  namespace           = "AWS/AutoScaling"
  period              = 60
  statistic           = "Average"
  threshold           = var.min_instances
  alarm_description   = "ASG has fewer than ${var.min_instances} healthy instances"

  dimensions = {
    AutoScalingGroupName = var.asg_name
  }

  alarm_actions = var.alarm_sns_topic_arn != "" ? [var.alarm_sns_topic_arn] : []

  tags = var.tags
}

# Alarm: High Backlog Per Instance (triggers scale-out)
resource "aws_cloudwatch_metric_alarm" "high_backlog" {
  alarm_name          = "${var.project_name}-high-backlog"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "BacklogPerInstance"
  namespace           = "BankingPlatform/SQS"
  period              = 60
  statistic           = "Average"
  threshold           = var.target_messages_per_instance * 2
  alarm_description   = "Backlog per instance exceeds ${var.target_messages_per_instance * 2}"

  dimensions = {
    QueueName            = "transaction-queue"
    AutoScalingGroupName = var.asg_name
  }

  alarm_actions = var.scale_out_policy_arn != "" ? [var.scale_out_policy_arn] : []

  tags = var.tags
}
