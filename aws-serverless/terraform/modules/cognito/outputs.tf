output "user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.main.arn
}

output "user_pool_endpoint" {
  description = "Cognito User Pool endpoint"
  value       = aws_cognito_user_pool.main.endpoint
}

output "client_id" {
  description = "Cognito App Client ID"
  value       = aws_cognito_user_pool_client.main.id
}

output "domain" {
  description = "Cognito domain"
  value       = aws_cognito_user_pool_domain.main.domain
}

output "identity_pool_id" {
  description = "Cognito Identity Pool ID"
  value       = var.create_identity_pool ? aws_cognito_identity_pool.main[0].id : null
}

output "issuer_url" {
  description = "Token issuer URL"
  value       = "https://${aws_cognito_user_pool.main.endpoint}"
}

output "jwks_url" {
  description = "JWKS URL for token validation"
  value       = "https://${aws_cognito_user_pool.main.endpoint}/.well-known/jwks.json"
}
