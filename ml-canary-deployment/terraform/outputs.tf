# Outputs for ML Canary Deployment

# API Gateway Outputs
output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "api_id" {
  description = "API Gateway REST API ID"
  value       = module.api_gateway.api_id
}

# SageMaker Outputs
output "endpoint_name" {
  description = "SageMaker endpoint name"
  value       = module.sagemaker.endpoint_name
}

output "endpoint_arn" {
  description = "SageMaker endpoint ARN"
  value       = module.sagemaker.endpoint_arn
}

output "endpoint_config_name" {
  description = "SageMaker endpoint configuration name"
  value       = module.sagemaker.endpoint_config_name
}

# S3 Outputs
output "model_bucket_name" {
  description = "S3 bucket for model artifacts"
  value       = module.s3.model_bucket_name
}

output "model_bucket_arn" {
  description = "S3 bucket ARN for model artifacts"
  value       = module.s3.model_bucket_arn
}

output "logs_bucket_name" {
  description = "S3 bucket for inference logs"
  value       = module.s3.logs_bucket_name
}

# DynamoDB Outputs
output "deployments_table_name" {
  description = "DynamoDB table for deployment records"
  value       = module.dynamodb.deployments_table_name
}

output "metrics_table_name" {
  description = "DynamoDB table for metrics"
  value       = module.dynamodb.metrics_table_name
}

output "events_table_name" {
  description = "DynamoDB table for deployment events"
  value       = module.dynamodb.events_table_name
}

# SNS Outputs
output "alerts_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = module.sns.alerts_topic_arn
}

output "events_topic_arn" {
  description = "SNS topic ARN for deployment events"
  value       = module.sns.events_topic_arn
}

# Lambda Outputs
output "api_handler_arn" {
  description = "API handler Lambda ARN"
  value       = module.lambda.api_handler_arn
}

output "deployment_handler_arn" {
  description = "Deployment handler Lambda ARN"
  value       = module.lambda.deployment_handler_arn
}

output "monitoring_handler_arn" {
  description = "Monitoring handler Lambda ARN"
  value       = module.lambda.monitoring_handler_arn
}

# IAM Outputs
output "lambda_execution_role_arn" {
  description = "Lambda execution role ARN"
  value       = module.iam.lambda_execution_role_arn
}

output "sagemaker_execution_role_arn" {
  description = "SageMaker execution role ARN"
  value       = module.iam.sagemaker_execution_role_arn
}

# CloudWatch Outputs
output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = module.cloudwatch.dashboard_name
}

# Convenience Outputs
output "inference_url" {
  description = "URL for inference API endpoint"
  value       = "${module.api_gateway.api_endpoint}/inference"
}

output "deployment_url" {
  description = "URL for deployment API endpoint"
  value       = "${module.api_gateway.api_endpoint}/deployments"
}
