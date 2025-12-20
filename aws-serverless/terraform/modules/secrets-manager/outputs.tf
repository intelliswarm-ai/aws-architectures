# =============================================================================
# Secrets Manager Module Outputs
# =============================================================================

output "secret_arns" {
  description = "Map of secret names to ARNs"
  value       = { for k, v in aws_secretsmanager_secret.this : k => v.arn }
}

output "secret_ids" {
  description = "Map of secret names to IDs"
  value       = { for k, v in aws_secretsmanager_secret.this : k => v.id }
}

output "tenant_secret_arns" {
  description = "Map of tenant secret names to ARNs"
  value       = { for k, v in aws_secretsmanager_secret.tenant : k => v.arn }
}

output "database_secret_arn" {
  description = "Database credentials secret ARN"
  value       = aws_secretsmanager_secret.database.arn
}

output "database_secret_name" {
  description = "Database credentials secret name"
  value       = aws_secretsmanager_secret.database.name
}

output "api_integrations_secret_arn" {
  description = "API integrations secret ARN"
  value       = aws_secretsmanager_secret.api_integrations.arn
}

output "oauth_secret_arn" {
  description = "OAuth credentials secret ARN"
  value       = aws_secretsmanager_secret.oauth.arn
}

output "email_secret_arn" {
  description = "Email service credentials secret ARN"
  value       = aws_secretsmanager_secret.email.arn
}

output "all_secret_arns" {
  description = "List of all secret ARNs for IAM policies"
  value = concat(
    [for v in aws_secretsmanager_secret.this : v.arn],
    [for v in aws_secretsmanager_secret.tenant : v.arn],
    [
      aws_secretsmanager_secret.database.arn,
      aws_secretsmanager_secret.api_integrations.arn,
      aws_secretsmanager_secret.oauth.arn,
      aws_secretsmanager_secret.email.arn
    ]
  )
}
