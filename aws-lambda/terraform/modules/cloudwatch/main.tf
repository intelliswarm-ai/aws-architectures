# CloudWatch Dashboard
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = var.dashboard_name

  dashboard_body = jsonencode({
    widgets = concat(
      # Lambda Metrics
      [
        {
          type   = "metric"
          x      = 0
          y      = 0
          width  = 12
          height = 6
          properties = {
            title  = "Lambda Invocations"
            region = var.aws_region
            metrics = [
              for lambda_name in var.lambda_function_names :
              ["AWS/Lambda", "Invocations", "FunctionName", lambda_name]
            ]
            stat   = "Sum"
            period = 60
            view   = "timeSeries"
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
            region = var.aws_region
            metrics = [
              for lambda_name in var.lambda_function_names :
              ["AWS/Lambda", "Errors", "FunctionName", lambda_name]
            ]
            stat   = "Sum"
            period = 60
            view   = "timeSeries"
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
            region = var.aws_region
            metrics = [
              for lambda_name in var.lambda_function_names :
              ["AWS/Lambda", "Duration", "FunctionName", lambda_name]
            ]
            stat   = "Average"
            period = 60
            view   = "timeSeries"
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
            region = var.aws_region
            metrics = [
              for lambda_name in var.lambda_function_names :
              ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", lambda_name]
            ]
            stat   = "Maximum"
            period = 60
            view   = "timeSeries"
          }
        }
      ],
      # SQS Metrics
      [
        {
          type   = "metric"
          x      = 0
          y      = 12
          width  = 8
          height = 6
          properties = {
            title  = "SQS Queue Depth"
            region = var.aws_region
            metrics = [
              ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.queue_name],
              ["AWS/SQS", "ApproximateNumberOfMessagesNotVisible", "QueueName", var.queue_name]
            ]
            stat   = "Average"
            period = 60
            view   = "timeSeries"
          }
        },
        {
          type   = "metric"
          x      = 8
          y      = 12
          width  = 8
          height = 6
          properties = {
            title  = "SQS Messages"
            region = var.aws_region
            metrics = [
              ["AWS/SQS", "NumberOfMessagesSent", "QueueName", var.queue_name],
              ["AWS/SQS", "NumberOfMessagesReceived", "QueueName", var.queue_name],
              ["AWS/SQS", "NumberOfMessagesDeleted", "QueueName", var.queue_name]
            ]
            stat   = "Sum"
            period = 60
            view   = "timeSeries"
          }
        },
        {
          type   = "metric"
          x      = 16
          y      = 12
          width  = 8
          height = 6
          properties = {
            title  = "DLQ Depth"
            region = var.aws_region
            metrics = [
              ["AWS/SQS", "ApproximateNumberOfMessagesVisible", "QueueName", var.dlq_name]
            ]
            stat   = "Average"
            period = 60
            view   = "timeSeries"
            annotations = {
              horizontal = [
                {
                  value = 1
                  color = "#d62728"
                  label = "Alert Threshold"
                }
              ]
            }
          }
        }
      ],
      # Step Functions Metrics
      [
        {
          type   = "metric"
          x      = 0
          y      = 18
          width  = 8
          height = 6
          properties = {
            title  = "Step Functions Executions"
            region = var.aws_region
            metrics = [
              ["AWS/States", "ExecutionsStarted", "StateMachineArn", var.state_machine_arn],
              ["AWS/States", "ExecutionsSucceeded", "StateMachineArn", var.state_machine_arn],
              ["AWS/States", "ExecutionsFailed", "StateMachineArn", var.state_machine_arn]
            ]
            stat   = "Sum"
            period = 60
            view   = "timeSeries"
          }
        },
        {
          type   = "metric"
          x      = 8
          y      = 18
          width  = 8
          height = 6
          properties = {
            title  = "Step Functions Duration"
            region = var.aws_region
            metrics = [
              ["AWS/States", "ExecutionTime", "StateMachineArn", var.state_machine_arn]
            ]
            stat   = "Average"
            period = 60
            view   = "timeSeries"
          }
        },
        {
          type   = "metric"
          x      = 16
          y      = 18
          width  = 8
          height = 6
          properties = {
            title  = "DynamoDB Consumed Capacity"
            region = var.aws_region
            metrics = [
              ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", var.table_name],
              ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", var.table_name]
            ]
            stat   = "Sum"
            period = 60
            view   = "timeSeries"
          }
        }
      ]
    )
  })
}

# Alarm: Lambda Errors
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${each.value}-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60
  statistic           = "Sum"
  threshold           = var.lambda_error_threshold
  alarm_description   = "Lambda function ${each.value} error rate is too high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = each.value
  }

  alarm_actions = var.alarm_sns_topic_arns
  ok_actions    = var.alarm_sns_topic_arns

  tags = var.tags
}

# Alarm: SQS DLQ has messages
resource "aws_cloudwatch_metric_alarm" "dlq_messages" {
  alarm_name          = "${var.dlq_name}-has-messages"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Average"
  threshold           = 0
  alarm_description   = "Dead letter queue ${var.dlq_name} has messages"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = var.dlq_name
  }

  alarm_actions = var.alarm_sns_topic_arns
  ok_actions    = var.alarm_sns_topic_arns

  tags = var.tags
}

# Alarm: Step Functions Failed Executions
resource "aws_cloudwatch_metric_alarm" "sfn_failures" {
  alarm_name          = "${var.state_machine_name}-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 60
  statistic           = "Sum"
  threshold           = var.sfn_failure_threshold
  alarm_description   = "Step Functions state machine ${var.state_machine_name} has too many failures"
  treat_missing_data  = "notBreaching"

  dimensions = {
    StateMachineArn = var.state_machine_arn
  }

  alarm_actions = var.alarm_sns_topic_arns
  ok_actions    = var.alarm_sns_topic_arns

  tags = var.tags
}

# Alarm: SQS Queue Depth
resource "aws_cloudwatch_metric_alarm" "queue_depth" {
  alarm_name          = "${var.queue_name}-high-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "ApproximateNumberOfMessagesVisible"
  namespace           = "AWS/SQS"
  period              = 60
  statistic           = "Average"
  threshold           = var.queue_depth_threshold
  alarm_description   = "SQS queue ${var.queue_name} depth is too high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    QueueName = var.queue_name
  }

  alarm_actions = var.alarm_sns_topic_arns
  ok_actions    = var.alarm_sns_topic_arns

  tags = var.tags
}
