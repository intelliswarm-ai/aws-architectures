output "model_bucket_name" {
  description = "Model artifacts bucket name"
  value       = aws_s3_bucket.model_artifacts.id
}

output "model_bucket_arn" {
  description = "Model artifacts bucket ARN"
  value       = aws_s3_bucket.model_artifacts.arn
}

output "logs_bucket_name" {
  description = "Inference logs bucket name"
  value       = aws_s3_bucket.inference_logs.id
}

output "logs_bucket_arn" {
  description = "Inference logs bucket ARN"
  value       = aws_s3_bucket.inference_logs.arn
}
