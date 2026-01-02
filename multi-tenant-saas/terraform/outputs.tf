# =============================================================================
# AWS Serverless Enterprise Platform - Outputs
# =============================================================================

# -----------------------------------------------------------------------------
# General
# -----------------------------------------------------------------------------

output "environment" {
  description = "Deployment environment"
  value       = var.environment
}

output "region" {
  description = "AWS region"
  value       = var.aws_region
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "VPC ID"
  value       = var.enable_vpc ? module.vpc[0].vpc_id : null
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = var.enable_vpc ? module.vpc[0].private_subnet_ids : []
}

output "lambda_security_group_id" {
  description = "Lambda security group ID"
  value       = var.enable_vpc ? module.security_groups[0].lambda_sg_id : null
}

# -----------------------------------------------------------------------------
# Cognito
# -----------------------------------------------------------------------------

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = var.enable_cognito ? module.cognito[0].user_pool_id : null
}

output "cognito_client_id" {
  description = "Cognito App Client ID"
  value       = var.enable_cognito ? module.cognito[0].client_id : null
}

output "cognito_domain" {
  description = "Cognito domain"
  value       = var.enable_cognito ? module.cognito[0].domain : null
}

output "cognito_issuer_url" {
  description = "Cognito issuer URL for JWT validation"
  value       = var.enable_cognito ? module.cognito[0].issuer_url : null
}

# -----------------------------------------------------------------------------
# DynamoDB
# -----------------------------------------------------------------------------

output "tenant_table_name" {
  description = "Tenant DynamoDB table name"
  value       = module.dynamodb.table_name
}

output "tenant_table_arn" {
  description = "Tenant DynamoDB table ARN"
  value       = module.dynamodb.table_arn
}

output "audit_table_name" {
  description = "Audit DynamoDB table name"
  value       = var.enable_audit_logging ? module.dynamodb_audit[0].table_name : null
}

# -----------------------------------------------------------------------------
# SQS
# -----------------------------------------------------------------------------

output "processing_queue_url" {
  description = "Processing queue URL"
  value       = module.sqs.queue_url
}

output "processing_queue_arn" {
  description = "Processing queue ARN"
  value       = module.sqs.queue_arn
}

output "dlq_url" {
  description = "Dead letter queue URL"
  value       = module.sqs.dlq_url
}

# -----------------------------------------------------------------------------
# SNS
# -----------------------------------------------------------------------------

output "notification_topic_arn" {
  description = "Notification SNS topic ARN"
  value       = module.sns.notification_topic_arn
}

output "alert_topic_arn" {
  description = "Alert SNS topic ARN"
  value       = module.sns.alert_topic_arn
}

# -----------------------------------------------------------------------------
# EventBridge
# -----------------------------------------------------------------------------

output "event_bus_name" {
  description = "EventBridge event bus name"
  value       = module.eventbridge.event_bus_name
}

output "event_bus_arn" {
  description = "EventBridge event bus ARN"
  value       = module.eventbridge.event_bus_arn
}

# -----------------------------------------------------------------------------
# KMS
# -----------------------------------------------------------------------------

output "kms_key_id" {
  description = "KMS key ID"
  value       = var.enable_encryption ? module.kms[0].key_id : null
}

output "kms_key_arn" {
  description = "KMS key ARN"
  value       = var.enable_encryption ? module.kms[0].key_arn : null
}
