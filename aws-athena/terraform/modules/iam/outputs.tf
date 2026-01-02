output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = aws_iam_role.lambda.arn
}

output "lambda_role_name" {
  description = "Name of the Lambda execution role"
  value       = aws_iam_role.lambda.name
}

output "glue_role_arn" {
  description = "ARN of the Glue service role"
  value       = aws_iam_role.glue.arn
}

output "glue_role_name" {
  description = "Name of the Glue service role"
  value       = aws_iam_role.glue.name
}

output "lakeformation_role_arn" {
  description = "ARN of the Lake Formation service role"
  value       = var.enable_lakeformation ? aws_iam_role.lakeformation[0].arn : null
}
