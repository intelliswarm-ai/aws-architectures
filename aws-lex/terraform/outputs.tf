output "lex_bot_id" {
  description = "Lex bot ID"
  value       = module.lex.bot_id
}

output "lex_bot_alias_id" {
  description = "Lex bot alias ID"
  value       = module.lex.bot_alias_id
}

output "lex_bot_locale" {
  description = "Lex bot locale"
  value       = var.bot_locale
}

output "fulfillment_lambda_arn" {
  description = "Fulfillment Lambda function ARN"
  value       = module.lambda.fulfillment_lambda_arn
}

output "bookings_table_name" {
  description = "DynamoDB bookings table name"
  value       = module.dynamodb.bookings_table_name
}

output "flights_table_name" {
  description = "DynamoDB flights table name"
  value       = module.dynamodb.flights_table_name
}

output "checkins_table_name" {
  description = "DynamoDB check-ins table name"
  value       = module.dynamodb.checkins_table_name
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.cloudwatch.dashboard_url
}

output "test_command" {
  description = "AWS CLI command to test the bot"
  value       = <<-EOT
    aws lexv2-runtime recognize-text \
      --bot-id ${module.lex.bot_id} \
      --bot-alias-id ${module.lex.bot_alias_id} \
      --locale-id ${var.bot_locale} \
      --session-id test-session \
      --text "I want to book a flight"
  EOT
}
