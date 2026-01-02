output "role_arn" {
  value = aws_iam_role.sagemaker_exec.arn
}

output "role_name" {
  value = aws_iam_role.sagemaker_exec.name
}
