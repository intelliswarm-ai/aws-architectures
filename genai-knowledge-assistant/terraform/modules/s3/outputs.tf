output "documents_bucket_name" {
  description = "Documents bucket name"
  value       = aws_s3_bucket.documents.id
}

output "documents_bucket_arn" {
  description = "Documents bucket ARN"
  value       = aws_s3_bucket.documents.arn
}

output "documents_bucket_domain" {
  description = "Documents bucket domain name"
  value       = aws_s3_bucket.documents.bucket_domain_name
}
