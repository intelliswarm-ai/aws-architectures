output "workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = aws_athena_workgroup.main.name
}

output "workgroup_arn" {
  description = "ARN of the Athena workgroup"
  value       = aws_athena_workgroup.main.arn
}

output "results_location" {
  description = "S3 location for query results"
  value       = "s3://${var.results_bucket_name}/athena-results/"
}
