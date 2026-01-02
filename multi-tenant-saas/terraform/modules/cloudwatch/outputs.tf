output "log_group_name" {
  value = aws_cloudwatch_log_group.lambda.name
}

output "log_group_arn" {
  value = aws_cloudwatch_log_group.lambda.arn
}
