output "api_handler_arn" {
  description = "API handler Lambda ARN"
  value       = aws_lambda_function.api_handler.arn
}

output "api_handler_name" {
  description = "API handler Lambda name"
  value       = aws_lambda_function.api_handler.function_name
}

output "deployment_handler_arn" {
  description = "Deployment handler Lambda ARN"
  value       = aws_lambda_function.deployment_handler.arn
}

output "deployment_handler_name" {
  description = "Deployment handler Lambda name"
  value       = aws_lambda_function.deployment_handler.function_name
}

output "monitoring_handler_arn" {
  description = "Monitoring handler Lambda ARN"
  value       = aws_lambda_function.monitoring_handler.arn
}

output "monitoring_handler_name" {
  description = "Monitoring handler Lambda name"
  value       = aws_lambda_function.monitoring_handler.function_name
}

output "traffic_shift_handler_arn" {
  description = "Traffic shift handler Lambda ARN"
  value       = aws_lambda_function.traffic_shift_handler.arn
}

output "traffic_shift_handler_name" {
  description = "Traffic shift handler Lambda name"
  value       = aws_lambda_function.traffic_shift_handler.function_name
}

output "rollback_handler_arn" {
  description = "Rollback handler Lambda ARN"
  value       = aws_lambda_function.rollback_handler.arn
}

output "rollback_handler_name" {
  description = "Rollback handler Lambda name"
  value       = aws_lambda_function.rollback_handler.function_name
}
