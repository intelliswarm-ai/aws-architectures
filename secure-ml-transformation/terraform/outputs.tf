################################################################################
# VPC Outputs
################################################################################

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

################################################################################
# S3 Outputs
################################################################################

output "raw_data_bucket" {
  description = "Raw data S3 bucket name"
  value       = module.s3.raw_data_bucket_name
}

output "processed_data_bucket" {
  description = "Processed data S3 bucket name"
  value       = module.s3.processed_data_bucket_name
}

output "scripts_bucket" {
  description = "Scripts S3 bucket name"
  value       = module.s3.scripts_bucket_name
}

################################################################################
# Glue Outputs
################################################################################

output "glue_database_name" {
  description = "Glue catalog database name"
  value       = module.glue.database_name
}

output "glue_job_name" {
  description = "Main Glue ETL job name"
  value       = module.glue.main_etl_job_name
}

output "glue_connection_name" {
  description = "Glue VPC connection name"
  value       = module.glue.connection_name
}

################################################################################
# Security Outputs
################################################################################

output "kms_key_id" {
  description = "KMS key ID"
  value       = module.kms.key_id
}

output "kms_key_arn" {
  description = "KMS key ARN"
  value       = module.kms.key_arn
}

################################################################################
# IAM Outputs
################################################################################

output "glue_role_arn" {
  description = "Glue service role ARN"
  value       = module.iam.glue_role_arn
}

output "lambda_role_arn" {
  description = "Lambda execution role ARN"
  value       = module.iam.lambda_role_arn
}

################################################################################
# CloudWatch Outputs
################################################################################

output "audit_log_group_name" {
  description = "Audit log group name"
  value       = module.cloudwatch.audit_log_group_name
}

output "dashboard_name" {
  description = "CloudWatch dashboard name"
  value       = module.cloudwatch.dashboard_name
}
