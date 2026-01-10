output "documents_table_name" {
  description = "Documents table name"
  value       = aws_dynamodb_table.documents.name
}

output "documents_table_arn" {
  description = "Documents table ARN"
  value       = aws_dynamodb_table.documents.arn
}

output "conversations_table_name" {
  description = "Conversations table name"
  value       = aws_dynamodb_table.conversations.name
}

output "conversations_table_arn" {
  description = "Conversations table ARN"
  value       = aws_dynamodb_table.conversations.arn
}
