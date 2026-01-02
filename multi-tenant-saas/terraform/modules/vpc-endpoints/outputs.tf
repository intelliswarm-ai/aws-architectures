# =============================================================================
# VPC Endpoints Module Outputs
# =============================================================================

output "s3_endpoint_id" {
  description = "S3 gateway endpoint ID"
  value       = var.enable_s3_endpoint ? aws_vpc_endpoint.s3[0].id : null
}

output "dynamodb_endpoint_id" {
  description = "DynamoDB gateway endpoint ID"
  value       = var.enable_dynamodb_endpoint ? aws_vpc_endpoint.dynamodb[0].id : null
}

output "secretsmanager_endpoint_id" {
  description = "Secrets Manager interface endpoint ID"
  value       = var.enable_secrets_manager_endpoint ? aws_vpc_endpoint.secretsmanager[0].id : null
}

output "ssm_endpoint_id" {
  description = "SSM interface endpoint ID"
  value       = var.enable_ssm_endpoint ? aws_vpc_endpoint.ssm[0].id : null
}

output "sqs_endpoint_id" {
  description = "SQS interface endpoint ID"
  value       = var.enable_sqs_endpoint ? aws_vpc_endpoint.sqs[0].id : null
}

output "sns_endpoint_id" {
  description = "SNS interface endpoint ID"
  value       = var.enable_sns_endpoint ? aws_vpc_endpoint.sns[0].id : null
}

output "kms_endpoint_id" {
  description = "KMS interface endpoint ID"
  value       = var.enable_kms_endpoint ? aws_vpc_endpoint.kms[0].id : null
}

output "logs_endpoint_id" {
  description = "CloudWatch Logs interface endpoint ID"
  value       = var.enable_logs_endpoint ? aws_vpc_endpoint.logs[0].id : null
}

output "events_endpoint_id" {
  description = "EventBridge interface endpoint ID"
  value       = var.enable_events_endpoint ? aws_vpc_endpoint.events[0].id : null
}

output "bedrock_endpoint_id" {
  description = "Bedrock interface endpoint ID"
  value       = var.enable_bedrock_endpoint ? aws_vpc_endpoint.bedrock[0].id : null
}

output "execute_api_endpoint_id" {
  description = "API Gateway execute-api interface endpoint ID"
  value       = var.enable_execute_api_endpoint ? aws_vpc_endpoint.execute_api[0].id : null
}

output "all_endpoint_ids" {
  description = "List of all endpoint IDs"
  value = compact([
    var.enable_s3_endpoint ? aws_vpc_endpoint.s3[0].id : null,
    var.enable_dynamodb_endpoint ? aws_vpc_endpoint.dynamodb[0].id : null,
    var.enable_secrets_manager_endpoint ? aws_vpc_endpoint.secretsmanager[0].id : null,
    var.enable_ssm_endpoint ? aws_vpc_endpoint.ssm[0].id : null,
    var.enable_sqs_endpoint ? aws_vpc_endpoint.sqs[0].id : null,
    var.enable_sns_endpoint ? aws_vpc_endpoint.sns[0].id : null,
    var.enable_kms_endpoint ? aws_vpc_endpoint.kms[0].id : null,
    var.enable_logs_endpoint ? aws_vpc_endpoint.logs[0].id : null,
    var.enable_events_endpoint ? aws_vpc_endpoint.events[0].id : null,
    var.enable_bedrock_endpoint ? aws_vpc_endpoint.bedrock[0].id : null,
    var.enable_execute_api_endpoint ? aws_vpc_endpoint.execute_api[0].id : null
  ])
}
