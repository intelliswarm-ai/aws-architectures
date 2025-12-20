# =============================================================================
# CloudTrail Module Outputs
# =============================================================================

output "trail_id" {
  description = "CloudTrail trail ID"
  value       = aws_cloudtrail.this.id
}

output "trail_arn" {
  description = "CloudTrail trail ARN"
  value       = aws_cloudtrail.this.arn
}

output "trail_name" {
  description = "CloudTrail trail name"
  value       = aws_cloudtrail.this.name
}

output "trail_home_region" {
  description = "CloudTrail trail home region"
  value       = aws_cloudtrail.this.home_region
}

output "s3_bucket_name" {
  description = "S3 bucket name for CloudTrail logs"
  value       = var.s3_bucket_name != "" ? var.s3_bucket_name : aws_s3_bucket.cloudtrail[0].id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN for CloudTrail logs"
  value       = var.s3_bucket_name != "" ? "arn:aws:s3:::${var.s3_bucket_name}" : aws_s3_bucket.cloudtrail[0].arn
}

output "cloudwatch_log_group_name" {
  description = "CloudWatch log group name"
  value       = var.enable_cloudwatch_logs ? aws_cloudwatch_log_group.cloudtrail[0].name : null
}

output "cloudwatch_log_group_arn" {
  description = "CloudWatch log group ARN"
  value       = var.enable_cloudwatch_logs ? aws_cloudwatch_log_group.cloudtrail[0].arn : null
}

output "cloudwatch_role_arn" {
  description = "IAM role ARN for CloudWatch Logs"
  value       = var.enable_cloudwatch_logs ? aws_iam_role.cloudtrail_cloudwatch[0].arn : null
}
