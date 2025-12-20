# =============================================================================
# AWS Budgets Module Outputs
# =============================================================================

output "monthly_budget_id" {
  description = "Monthly budget ID"
  value       = aws_budgets_budget.monthly.id
}

output "monthly_budget_name" {
  description = "Monthly budget name"
  value       = aws_budgets_budget.monthly.name
}

output "lambda_budget_id" {
  description = "Lambda budget ID"
  value       = var.enable_lambda_budget ? aws_budgets_budget.lambda[0].id : null
}

output "dynamodb_budget_id" {
  description = "DynamoDB budget ID"
  value       = var.enable_dynamodb_budget ? aws_budgets_budget.dynamodb[0].id : null
}

output "api_gateway_budget_id" {
  description = "API Gateway budget ID"
  value       = var.enable_api_gateway_budget ? aws_budgets_budget.api_gateway[0].id : null
}

output "anomaly_monitor_arn" {
  description = "Cost anomaly monitor ARN"
  value       = aws_ce_anomaly_monitor.this.arn
}

output "anomaly_subscription_id" {
  description = "Cost anomaly subscription ID"
  value       = var.notification_email != "" ? aws_ce_anomaly_subscription.this[0].id : null
}
