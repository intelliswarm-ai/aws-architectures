output "glue_role_arn" {
  description = "Glue service role ARN"
  value       = aws_iam_role.glue.arn
}

output "glue_role_name" {
  description = "Glue service role name"
  value       = aws_iam_role.glue.name
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda.arn
}

output "lambda_role_name" {
  description = "Lambda execution role name"
  value       = aws_iam_role.lambda.name
}

output "databrew_role_arn" {
  description = "DataBrew service role ARN"
  value       = aws_iam_role.databrew.arn
}

output "databrew_role_name" {
  description = "DataBrew service role name"
  value       = aws_iam_role.databrew.name
}
