output "ingest_function_arn" {
  description = "ARN of the ingest function"
  value       = aws_lambda_function.ingest.arn
}

output "ingest_function_name" {
  description = "Name of the ingest function"
  value       = aws_lambda_function.ingest.function_name
}

output "ingest_function_url" {
  description = "URL of the ingest function"
  value       = aws_lambda_function_url.ingest.function_url
}

output "etl_function_arn" {
  description = "ARN of the ETL function"
  value       = aws_lambda_function.etl.arn
}

output "etl_function_name" {
  description = "Name of the ETL function"
  value       = aws_lambda_function.etl.function_name
}

output "etl_function_url" {
  description = "URL of the ETL function"
  value       = aws_lambda_function_url.etl.function_url
}

output "query_function_arn" {
  description = "ARN of the query function"
  value       = aws_lambda_function.query.arn
}

output "query_function_name" {
  description = "Name of the query function"
  value       = aws_lambda_function.query.function_name
}

output "query_function_url" {
  description = "URL of the query function"
  value       = aws_lambda_function_url.query.function_url
}

output "api_function_arn" {
  description = "ARN of the API function"
  value       = aws_lambda_function.api.arn
}

output "api_function_name" {
  description = "Name of the API function"
  value       = aws_lambda_function.api.function_name
}

output "api_function_url" {
  description = "URL of the API function"
  value       = aws_lambda_function_url.api.function_url
}

output "function_names" {
  description = "List of all Lambda function names"
  value = [
    aws_lambda_function.ingest.function_name,
    aws_lambda_function.etl.function_name,
    aws_lambda_function.query.function_name,
    aws_lambda_function.api.function_name,
  ]
}
