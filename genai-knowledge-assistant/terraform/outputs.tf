# =============================================================================
# GenAI Knowledge Assistant - Terraform Outputs
# =============================================================================

# =============================================================================
# API Gateway Outputs
# =============================================================================

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "api_id" {
  description = "API Gateway REST API ID"
  value       = module.api_gateway.api_id
}

# =============================================================================
# S3 Outputs
# =============================================================================

output "documents_bucket_name" {
  description = "S3 bucket name for documents"
  value       = module.s3.documents_bucket_name
}

output "documents_bucket_arn" {
  description = "S3 bucket ARN for documents"
  value       = module.s3.documents_bucket_arn
}

# =============================================================================
# DynamoDB Outputs
# =============================================================================

output "documents_table_name" {
  description = "DynamoDB table name for documents"
  value       = module.dynamodb.documents_table_name
}

output "conversations_table_name" {
  description = "DynamoDB table name for conversations"
  value       = module.dynamodb.conversations_table_name
}

# =============================================================================
# OpenSearch Outputs
# =============================================================================

output "opensearch_collection_endpoint" {
  description = "OpenSearch Serverless collection endpoint"
  value       = module.opensearch.collection_endpoint
}

output "opensearch_collection_arn" {
  description = "OpenSearch Serverless collection ARN"
  value       = module.opensearch.collection_arn
}

output "opensearch_dashboard_endpoint" {
  description = "OpenSearch Serverless dashboard endpoint"
  value       = module.opensearch.dashboard_endpoint
}

# =============================================================================
# Lambda Outputs
# =============================================================================

output "lambda_function_names" {
  description = "Names of all Lambda functions"
  value       = module.lambda.function_names
}

output "api_handler_arn" {
  description = "API handler Lambda ARN"
  value       = module.lambda.api_handler_arn
}

# =============================================================================
# Bedrock Outputs
# =============================================================================

output "knowledge_base_id" {
  description = "Bedrock Knowledge Base ID"
  value       = var.create_knowledge_base ? module.bedrock[0].knowledge_base_id : null
}

output "knowledge_base_data_source_id" {
  description = "Bedrock Knowledge Base Data Source ID"
  value       = var.create_knowledge_base ? module.bedrock[0].data_source_id : null
}

output "agent_id" {
  description = "Bedrock Agent ID"
  value       = var.enable_bedrock_agent && var.create_knowledge_base ? module.bedrock[0].agent_id : null
}

output "agent_alias_id" {
  description = "Bedrock Agent Alias ID"
  value       = var.enable_bedrock_agent && var.create_knowledge_base ? module.bedrock[0].agent_alias_id : null
}

# =============================================================================
# CloudWatch Outputs
# =============================================================================

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.cloudwatch.dashboard_url
}

output "log_group_names" {
  description = "CloudWatch log group names"
  value       = module.cloudwatch.log_group_names
}

# =============================================================================
# Summary Output
# =============================================================================

output "deployment_summary" {
  description = "Summary of deployed resources"
  value = {
    project     = var.project_name
    environment = var.environment
    region      = var.aws_region

    endpoints = {
      api       = module.api_gateway.api_endpoint
      dashboard = module.cloudwatch.dashboard_url
    }

    resources = {
      documents_bucket = module.s3.documents_bucket_name
      documents_table  = module.dynamodb.documents_table_name
      opensearch       = module.opensearch.collection_endpoint
    }

    bedrock = {
      knowledge_base_id = var.create_knowledge_base ? module.bedrock[0].knowledge_base_id : "not created"
      agent_id          = var.enable_bedrock_agent && var.create_knowledge_base ? module.bedrock[0].agent_id : "not created"
      model_id          = var.bedrock_model_id
    }
  }
}
