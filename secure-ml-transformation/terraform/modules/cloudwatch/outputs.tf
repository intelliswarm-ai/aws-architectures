output "audit_log_group_name" {
  description = "Audit log group name"
  value       = aws_cloudwatch_log_group.audit.name
}

output "audit_log_group_arn" {
  description = "Audit log group ARN"
  value       = aws_cloudwatch_log_group.audit.arn
}

output "etl_log_group_name" {
  description = "ETL log group name"
  value       = aws_cloudwatch_log_group.etl.name
}

output "databrew_log_group_name" {
  description = "DataBrew log group name"
  value       = aws_cloudwatch_log_group.databrew.name
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}
