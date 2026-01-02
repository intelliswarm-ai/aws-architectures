output "producer_function_name" {
  description = "Name of the producer function"
  value       = aws_lambda_function.producer.function_name
}

output "producer_function_arn" {
  description = "ARN of the producer function"
  value       = aws_lambda_function.producer.arn
}

output "dashboard_consumer_function_name" {
  description = "Name of the dashboard consumer function"
  value       = aws_lambda_function.dashboard_consumer.function_name
}

output "dashboard_consumer_function_arn" {
  description = "ARN of the dashboard consumer function"
  value       = aws_lambda_function.dashboard_consumer.arn
}

output "geofence_consumer_function_name" {
  description = "Name of the geofence consumer function"
  value       = aws_lambda_function.geofence_consumer.function_name
}

output "geofence_consumer_function_arn" {
  description = "ARN of the geofence consumer function"
  value       = aws_lambda_function.geofence_consumer.arn
}

output "archive_consumer_function_name" {
  description = "Name of the archive consumer function"
  value       = aws_lambda_function.archive_consumer.function_name
}

output "archive_consumer_function_arn" {
  description = "ARN of the archive consumer function"
  value       = aws_lambda_function.archive_consumer.arn
}
