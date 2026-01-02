output "transcripts_bucket" {
  description = "S3 bucket for call transcripts"
  value       = module.s3.transcripts_bucket_name
}

output "output_bucket" {
  description = "S3 bucket for Comprehend output"
  value       = module.s3.output_bucket_name
}

output "opensearch_endpoint" {
  description = "OpenSearch domain endpoint"
  value       = module.opensearch.domain_endpoint
}

output "opensearch_dashboard_url" {
  description = "OpenSearch Dashboards URL"
  value       = "https://${module.opensearch.domain_endpoint}/_dashboards"
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "api_key" {
  description = "API Gateway API key"
  value       = module.api_gateway.api_key
  sensitive   = true
}

output "lambda_functions" {
  description = "Lambda function names"
  value = {
    transcript_processor = module.lambda.transcript_processor_function_name
    comprehend_handler   = module.lambda.comprehend_handler_function_name
    result_indexer       = module.lambda.result_indexer_function_name
    api_handler          = module.lambda.api_handler_function_name
  }
}

output "comprehend_role_arn" {
  description = "IAM role ARN for Comprehend jobs"
  value       = module.iam.comprehend_role_arn
}
