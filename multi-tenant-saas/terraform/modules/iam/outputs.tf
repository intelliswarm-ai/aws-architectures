# =============================================================================
# IAM Module Outputs
# =============================================================================

output "permission_boundary_arn" {
  description = "Permission boundary policy ARN"
  value       = var.enable_permission_boundary ? aws_iam_policy.permission_boundary[0].arn : null
}

output "lambda_execution_role_arn" {
  description = "Lambda execution role ARN"
  value       = aws_iam_role.lambda_execution.arn
}

output "lambda_execution_role_name" {
  description = "Lambda execution role name"
  value       = aws_iam_role.lambda_execution.name
}

output "secrets_rotation_role_arn" {
  description = "Secrets rotation Lambda role ARN"
  value       = aws_iam_role.secrets_rotation.arn
}

output "secrets_rotation_role_name" {
  description = "Secrets rotation Lambda role name"
  value       = aws_iam_role.secrets_rotation.name
}

output "cross_account_role_arn" {
  description = "Cross-account access role ARN"
  value       = var.enable_cross_account && length(var.trusted_account_ids) > 0 ? aws_iam_role.cross_account[0].arn : null
}

output "multi_tenant_data_policy_arn" {
  description = "Multi-tenant data access policy ARN"
  value       = aws_iam_policy.multi_tenant_data_access.arn
}

output "secrets_access_policy_arn" {
  description = "Secrets access policy ARN"
  value       = aws_iam_policy.secrets_access.arn
}

output "bedrock_access_policy_arn" {
  description = "Bedrock GenAI access policy ARN"
  value       = aws_iam_policy.bedrock_access.arn
}

output "eventbridge_access_policy_arn" {
  description = "EventBridge access policy ARN"
  value       = aws_iam_policy.eventbridge_access.arn
}
