output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda.arn
}

output "lambda_role_name" {
  description = "Lambda execution role name"
  value       = aws_iam_role.lambda.name
}

output "bedrock_kb_role_arn" {
  description = "Bedrock Knowledge Base role ARN"
  value       = aws_iam_role.bedrock_kb.arn
}

output "bedrock_agent_role_arn" {
  description = "Bedrock Agent role ARN"
  value       = aws_iam_role.bedrock_agent.arn
}
