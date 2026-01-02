# ---------------------------------------------------------------------------------------------------------------------
# S3 OUTPUTS
# ---------------------------------------------------------------------------------------------------------------------

output "raw_bucket_name" {
  description = "Name of the raw data S3 bucket"
  value       = module.s3.raw_bucket_name
}

output "raw_bucket_arn" {
  description = "ARN of the raw data S3 bucket"
  value       = module.s3.raw_bucket_arn
}

output "processed_bucket_name" {
  description = "Name of the processed data S3 bucket"
  value       = module.s3.processed_bucket_name
}

output "processed_bucket_arn" {
  description = "ARN of the processed data S3 bucket"
  value       = module.s3.processed_bucket_arn
}

output "results_bucket_name" {
  description = "Name of the Athena results S3 bucket"
  value       = module.s3.results_bucket_name
}

# ---------------------------------------------------------------------------------------------------------------------
# GLUE OUTPUTS
# ---------------------------------------------------------------------------------------------------------------------

output "glue_database_name" {
  description = "Name of the Glue database"
  value       = module.glue.database_name
}

output "glue_etl_job_name" {
  description = "Name of the Glue ETL job"
  value       = module.glue.etl_job_name
}

output "glue_crawler_name" {
  description = "Name of the Glue crawler"
  value       = module.glue.crawler_name
}

# ---------------------------------------------------------------------------------------------------------------------
# ATHENA OUTPUTS
# ---------------------------------------------------------------------------------------------------------------------

output "athena_workgroup_name" {
  description = "Name of the Athena workgroup"
  value       = module.athena.workgroup_name
}

output "athena_results_location" {
  description = "S3 location for Athena query results"
  value       = module.athena.results_location
}

# ---------------------------------------------------------------------------------------------------------------------
# LAMBDA OUTPUTS
# ---------------------------------------------------------------------------------------------------------------------

output "ingest_function_arn" {
  description = "ARN of the ingest Lambda function"
  value       = module.lambda.ingest_function_arn
}

output "ingest_function_url" {
  description = "URL of the ingest Lambda function"
  value       = module.lambda.ingest_function_url
}

output "etl_function_arn" {
  description = "ARN of the ETL Lambda function"
  value       = module.lambda.etl_function_arn
}

output "query_function_arn" {
  description = "ARN of the query Lambda function"
  value       = module.lambda.query_function_arn
}

output "query_function_url" {
  description = "URL of the query Lambda function"
  value       = module.lambda.query_function_url
}

output "api_function_arn" {
  description = "ARN of the API Lambda function"
  value       = module.lambda.api_function_arn
}

output "api_function_url" {
  description = "URL of the API Lambda function"
  value       = module.lambda.api_function_url
}

# ---------------------------------------------------------------------------------------------------------------------
# IAM OUTPUTS
# ---------------------------------------------------------------------------------------------------------------------

output "lambda_role_arn" {
  description = "ARN of the Lambda execution role"
  value       = module.iam.lambda_role_arn
}

output "glue_role_arn" {
  description = "ARN of the Glue service role"
  value       = module.iam.glue_role_arn
}

# ---------------------------------------------------------------------------------------------------------------------
# LAKE FORMATION OUTPUTS
# ---------------------------------------------------------------------------------------------------------------------

output "lakeformation_enabled" {
  description = "Whether Lake Formation is enabled"
  value       = var.enable_lakeformation
}

# ---------------------------------------------------------------------------------------------------------------------
# CONFIGURATION OUTPUTS
# ---------------------------------------------------------------------------------------------------------------------

output "environment_config" {
  description = "Environment configuration for Lambda functions"
  value = {
    AWS_REGION            = var.aws_region
    RAW_BUCKET            = module.s3.raw_bucket_name
    PROCESSED_BUCKET      = module.s3.processed_bucket_name
    RESULTS_BUCKET        = module.s3.results_bucket_name
    GLUE_DATABASE         = var.glue_database_name
    ATHENA_WORKGROUP      = var.athena_workgroup_name
    GLUE_ETL_JOB_NAME     = var.glue_etl_job_name
    GLUE_CRAWLER_NAME     = var.glue_crawler_name
    ATHENA_QUERY_TIMEOUT  = var.athena_query_timeout
  }
}
