output "table_arn" {
  description = "ARN of the DynamoDB table"
  value       = aws_dynamodb_table.task_state.arn
}

output "table_name" {
  description = "Name of the DynamoDB table"
  value       = aws_dynamodb_table.task_state.name
}

output "table_id" {
  description = "ID of the DynamoDB table"
  value       = aws_dynamodb_table.task_state.id
}

output "stream_arn" {
  description = "ARN of the DynamoDB stream"
  value       = aws_dynamodb_table.task_state.stream_arn
}
