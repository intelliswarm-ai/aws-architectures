output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "dashboard_arn" {
  description = "CloudWatch dashboard ARN"
  value       = aws_cloudwatch_dashboard.main.dashboard_arn
}

output "latency_alarm_arn" {
  description = "Latency alarm ARN"
  value       = aws_cloudwatch_metric_alarm.latency_alarm.arn
}

output "error_alarm_arn" {
  description = "Error rate alarm ARN"
  value       = aws_cloudwatch_metric_alarm.error_alarm.arn
}

output "monitoring_rule_arn" {
  description = "Monitoring EventBridge rule ARN"
  value       = aws_cloudwatch_event_rule.monitoring_schedule.arn
}
