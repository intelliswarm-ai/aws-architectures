# =============================================================================
# API Gateway Module Outputs
# =============================================================================

output "rest_api_id" {
  description = "REST API ID"
  value       = aws_api_gateway_rest_api.this.id
}

output "rest_api_arn" {
  description = "REST API ARN"
  value       = aws_api_gateway_rest_api.this.arn
}

output "rest_api_name" {
  description = "REST API name"
  value       = aws_api_gateway_rest_api.this.name
}

output "execution_arn" {
  description = "REST API execution ARN"
  value       = aws_api_gateway_rest_api.this.execution_arn
}

output "stage_name" {
  description = "Deployment stage name"
  value       = aws_api_gateway_stage.this.stage_name
}

output "stage_arn" {
  description = "Stage ARN"
  value       = aws_api_gateway_stage.this.arn
}

output "invoke_url" {
  description = "API Gateway invoke URL"
  value       = aws_api_gateway_stage.this.invoke_url
}

output "api_key_id" {
  description = "API key ID"
  value       = var.enable_api_key ? aws_api_gateway_api_key.this[0].id : null
}

output "api_key_value" {
  description = "API key value"
  value       = var.enable_api_key ? aws_api_gateway_api_key.this[0].value : null
  sensitive   = true
}

output "usage_plan_id" {
  description = "Usage plan ID"
  value       = var.enable_api_key ? aws_api_gateway_usage_plan.this[0].id : null
}

output "cognito_authorizer_id" {
  description = "Cognito authorizer ID"
  value       = var.enable_cognito_authorizer ? aws_api_gateway_authorizer.cognito[0].id : null
}

output "lambda_authorizer_id" {
  description = "Lambda authorizer ID"
  value       = var.enable_lambda_authorizer ? aws_api_gateway_authorizer.lambda[0].id : null
}

output "log_group_name" {
  description = "Access log CloudWatch log group name"
  value       = var.enable_access_logging ? aws_cloudwatch_log_group.api_gateway[0].name : null
}
