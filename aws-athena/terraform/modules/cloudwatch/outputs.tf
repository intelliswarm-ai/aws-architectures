output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "lambda_error_alarm_arns" {
  description = "ARNs of Lambda error alarms"
  value       = { for k, v in aws_cloudwatch_metric_alarm.lambda_errors : k => v.arn }
}

output "athena_cost_alarm_arn" {
  description = "ARN of Athena cost alarm"
  value       = aws_cloudwatch_metric_alarm.athena_data_scanned.arn
}

output "glue_failure_alarm_arn" {
  description = "ARN of Glue failure alarm"
  value       = aws_cloudwatch_metric_alarm.glue_failures.arn
}
