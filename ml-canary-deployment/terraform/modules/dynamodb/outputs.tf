output "deployments_table_name" {
  description = "Deployments table name"
  value       = aws_dynamodb_table.deployments.name
}

output "deployments_table_arn" {
  description = "Deployments table ARN"
  value       = aws_dynamodb_table.deployments.arn
}

output "metrics_table_name" {
  description = "Metrics table name"
  value       = aws_dynamodb_table.metrics.name
}

output "metrics_table_arn" {
  description = "Metrics table ARN"
  value       = aws_dynamodb_table.metrics.arn
}

output "events_table_name" {
  description = "Events table name"
  value       = aws_dynamodb_table.events.name
}

output "events_table_arn" {
  description = "Events table ARN"
  value       = aws_dynamodb_table.events.arn
}
