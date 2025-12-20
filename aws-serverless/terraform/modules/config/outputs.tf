# =============================================================================
# AWS Config Module Outputs
# =============================================================================

output "recorder_id" {
  description = "Config recorder ID"
  value       = aws_config_configuration_recorder.this.id
}

output "recorder_name" {
  description = "Config recorder name"
  value       = aws_config_configuration_recorder.this.name
}

output "delivery_channel_id" {
  description = "Config delivery channel ID"
  value       = aws_config_delivery_channel.this.id
}

output "s3_bucket_name" {
  description = "S3 bucket name for Config logs"
  value       = var.s3_bucket_name != "" ? var.s3_bucket_name : aws_s3_bucket.config[0].id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN for Config logs"
  value       = var.s3_bucket_name != "" ? "arn:aws:s3:::${var.s3_bucket_name}" : aws_s3_bucket.config[0].arn
}

output "role_arn" {
  description = "IAM role ARN for Config"
  value       = aws_iam_role.config.arn
}

output "config_rules" {
  description = "Map of Config rule names to ARNs"
  value = merge(
    var.enable_encrypted_volumes ? { encrypted_volumes = aws_config_config_rule.encrypted_volumes[0].arn } : {},
    var.enable_s3_bucket_encryption ? { s3_encryption = aws_config_config_rule.s3_encryption[0].arn } : {},
    var.enable_root_mfa ? { root_mfa = aws_config_config_rule.root_mfa[0].arn } : {},
    var.enable_iam_password_policy ? { iam_password_policy = aws_config_config_rule.iam_password_policy[0].arn } : {},
    var.enable_rds_encryption ? { rds_encryption = aws_config_config_rule.rds_encryption[0].arn } : {},
    var.enable_cloudtrail_enabled ? { cloudtrail_enabled = aws_config_config_rule.cloudtrail_enabled[0].arn } : {}
  )
}
