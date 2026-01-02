################################################################################
# DynamoDB Module - Outputs
################################################################################

output "responses_table_name" {
  description = "Name of the SMS responses table"
  value       = aws_dynamodb_table.responses.name
}

output "responses_table_arn" {
  description = "ARN of the SMS responses table"
  value       = aws_dynamodb_table.responses.arn
}

output "subscribers_table_name" {
  description = "Name of the subscribers table"
  value       = aws_dynamodb_table.subscribers.name
}

output "subscribers_table_arn" {
  description = "ARN of the subscribers table"
  value       = aws_dynamodb_table.subscribers.arn
}
