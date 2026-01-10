output "api_handler_arn" {
  description = "API handler Lambda ARN"
  value       = aws_lambda_function.api_handler.arn
}

output "api_handler_name" {
  description = "API handler Lambda name"
  value       = aws_lambda_function.api_handler.function_name
}

output "query_handler_arn" {
  description = "Query handler Lambda ARN"
  value       = aws_lambda_function.query_handler.arn
}

output "query_handler_name" {
  description = "Query handler Lambda name"
  value       = aws_lambda_function.query_handler.function_name
}

output "ingestion_handler_arn" {
  description = "Ingestion handler Lambda ARN"
  value       = aws_lambda_function.ingestion_handler.arn
}

output "ingestion_handler_name" {
  description = "Ingestion handler Lambda name"
  value       = aws_lambda_function.ingestion_handler.function_name
}

output "agent_handler_arn" {
  description = "Agent handler Lambda ARN"
  value       = aws_lambda_function.agent_handler.arn
}

output "agent_handler_name" {
  description = "Agent handler Lambda name"
  value       = aws_lambda_function.agent_handler.function_name
}

output "sync_handler_arn" {
  description = "Sync handler Lambda ARN"
  value       = aws_lambda_function.sync_handler.arn
}

output "function_names" {
  description = "All Lambda function names"
  value = [
    aws_lambda_function.api_handler.function_name,
    aws_lambda_function.query_handler.function_name,
    aws_lambda_function.ingestion_handler.function_name,
    aws_lambda_function.agent_handler.function_name,
    aws_lambda_function.sync_handler.function_name,
  ]
}
