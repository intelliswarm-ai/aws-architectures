output "raw_data_bucket_name" {
  description = "Raw data bucket name"
  value       = aws_s3_bucket.raw_data.id
}

output "raw_data_bucket_arn" {
  description = "Raw data bucket ARN"
  value       = aws_s3_bucket.raw_data.arn
}

output "processed_data_bucket_name" {
  description = "Processed data bucket name"
  value       = aws_s3_bucket.processed_data.id
}

output "processed_data_bucket_arn" {
  description = "Processed data bucket ARN"
  value       = aws_s3_bucket.processed_data.arn
}

output "scripts_bucket_name" {
  description = "Scripts bucket name"
  value       = aws_s3_bucket.scripts.id
}

output "scripts_bucket_arn" {
  description = "Scripts bucket ARN"
  value       = aws_s3_bucket.scripts.arn
}
