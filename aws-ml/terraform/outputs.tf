# =============================================================================
# S3 Buckets
# =============================================================================

output "raw_bucket_name" {
  description = "Raw documents S3 bucket name"
  value       = module.s3.raw_bucket_name
}

output "raw_bucket_arn" {
  description = "Raw documents S3 bucket ARN"
  value       = module.s3.raw_bucket_arn
}

output "processed_bucket_name" {
  description = "Processed documents S3 bucket name"
  value       = module.s3.processed_bucket_name
}

output "model_bucket_name" {
  description = "Model artifacts S3 bucket name"
  value       = module.s3.model_bucket_name
}

# =============================================================================
# DynamoDB
# =============================================================================

output "documents_table_name" {
  description = "Documents DynamoDB table name"
  value       = module.dynamodb.documents_table_name
}

output "documents_table_arn" {
  description = "Documents DynamoDB table ARN"
  value       = module.dynamodb.documents_table_arn
}

# =============================================================================
# Lambda Functions
# =============================================================================

output "document_ingestion_function_name" {
  description = "Document ingestion Lambda function name"
  value       = module.lambda_ingestion.function_name
}

output "text_extraction_function_name" {
  description = "Text extraction Lambda function name"
  value       = module.lambda_extraction.function_name
}

output "bedrock_generation_function_name" {
  description = "Bedrock generation Lambda function name"
  value       = module.lambda_bedrock.function_name
}

# =============================================================================
# Step Functions
# =============================================================================

output "document_workflow_arn" {
  description = "Document processing workflow ARN"
  value       = module.step_functions.document_workflow_arn
}

output "document_workflow_name" {
  description = "Document processing workflow name"
  value       = module.step_functions.document_workflow_name
}

# =============================================================================
# SNS Topics
# =============================================================================

output "success_topic_arn" {
  description = "Success notification topic ARN"
  value       = module.sns.success_topic_arn
}

output "failure_topic_arn" {
  description = "Failure notification topic ARN"
  value       = module.sns.failure_topic_arn
}

# =============================================================================
# API Gateway
# =============================================================================

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

# =============================================================================
# SageMaker
# =============================================================================

output "sagemaker_endpoint_name" {
  description = "SageMaker endpoint name (if created)"
  value       = var.create_sagemaker_endpoint ? module.sagemaker[0].endpoint_name : null
}

output "sagemaker_role_arn" {
  description = "SageMaker execution role ARN"
  value       = module.sagemaker_iam.role_arn
}
