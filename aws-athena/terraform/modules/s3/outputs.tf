output "raw_bucket_name" {
  description = "Name of the raw data bucket"
  value       = aws_s3_bucket.raw.id
}

output "raw_bucket_arn" {
  description = "ARN of the raw data bucket"
  value       = aws_s3_bucket.raw.arn
}

output "processed_bucket_name" {
  description = "Name of the processed data bucket"
  value       = aws_s3_bucket.processed.id
}

output "processed_bucket_arn" {
  description = "ARN of the processed data bucket"
  value       = aws_s3_bucket.processed.arn
}

output "results_bucket_name" {
  description = "Name of the results bucket"
  value       = aws_s3_bucket.results.id
}

output "results_bucket_arn" {
  description = "ARN of the results bucket"
  value       = aws_s3_bucket.results.arn
}
