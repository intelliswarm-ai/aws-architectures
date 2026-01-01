################################################################################
# Lambda Module - Outputs
################################################################################

output "event_processor_function_name" {
  description = "Name of the event processor Lambda function"
  value       = aws_lambda_function.event_processor.function_name
}

output "event_processor_function_arn" {
  description = "ARN of the event processor Lambda function"
  value       = aws_lambda_function.event_processor.arn
}

output "response_handler_function_name" {
  description = "Name of the response handler Lambda function"
  value       = aws_lambda_function.response_handler.function_name
}

output "response_handler_function_arn" {
  description = "ARN of the response handler Lambda function"
  value       = aws_lambda_function.response_handler.arn
}

output "analytics_processor_function_name" {
  description = "Name of the analytics processor Lambda function"
  value       = aws_lambda_function.analytics_processor.function_name
}

output "analytics_processor_function_arn" {
  description = "ARN of the analytics processor Lambda function"
  value       = aws_lambda_function.analytics_processor.arn
}

output "archive_consumer_function_name" {
  description = "Name of the archive consumer Lambda function"
  value       = aws_lambda_function.archive_consumer.function_name
}

output "archive_consumer_function_arn" {
  description = "ARN of the archive consumer Lambda function"
  value       = aws_lambda_function.archive_consumer.arn
}
