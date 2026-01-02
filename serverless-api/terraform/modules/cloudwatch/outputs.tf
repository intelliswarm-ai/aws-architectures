output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_arn" {
  description = "ARN of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_arn
}

output "lambda_error_alarms" {
  description = "Map of Lambda function names to alarm ARNs"
  value       = { for k, v in aws_cloudwatch_metric_alarm.lambda_errors : k => v.arn }
}

output "dlq_alarm_arn" {
  description = "ARN of the DLQ alarm"
  value       = aws_cloudwatch_metric_alarm.dlq_messages.arn
}

output "sfn_failures_alarm_arn" {
  description = "ARN of the Step Functions failure alarm"
  value       = aws_cloudwatch_metric_alarm.sfn_failures.arn
}

output "queue_depth_alarm_arn" {
  description = "ARN of the queue depth alarm"
  value       = aws_cloudwatch_metric_alarm.queue_depth.arn
}
