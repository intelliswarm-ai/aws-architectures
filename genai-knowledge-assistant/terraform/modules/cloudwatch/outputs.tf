output "dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = "https://${data.aws_region.current.name}.console.aws.amazon.com/cloudwatch/home?region=${data.aws_region.current.name}#dashboards:name=${aws_cloudwatch_dashboard.main.dashboard_name}"
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "log_group_names" {
  description = "CloudWatch log group names"
  value = {
    application = aws_cloudwatch_log_group.application.name
  }
}

output "alarm_arns" {
  description = "CloudWatch alarm ARNs"
  value = {
    api_5xx    = aws_cloudwatch_metric_alarm.api_5xx.arn
    api_latency = aws_cloudwatch_metric_alarm.api_latency.arn
  }
}
