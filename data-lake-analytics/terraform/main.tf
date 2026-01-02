# ---------------------------------------------------------------------------------------------------------------------
# AWS ATHENA DATA LAKE INFRASTRUCTURE
# This Terraform configuration creates a complete data lake analytics platform
# ---------------------------------------------------------------------------------------------------------------------

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = merge(var.tags, {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    })
  }
}

# ---------------------------------------------------------------------------------------------------------------------
# DATA SOURCES
# ---------------------------------------------------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# ---------------------------------------------------------------------------------------------------------------------
# LOCAL VALUES
# ---------------------------------------------------------------------------------------------------------------------

locals {
  account_id = data.aws_caller_identity.current.account_id
  region     = data.aws_region.current.name

  name_prefix = "${var.project_name}-${var.environment}"

  raw_bucket_name       = var.raw_bucket_name != "" ? var.raw_bucket_name : "${local.name_prefix}-raw-${local.account_id}"
  processed_bucket_name = var.processed_bucket_name != "" ? var.processed_bucket_name : "${local.name_prefix}-processed-${local.account_id}"
  results_bucket_name   = var.results_bucket_name != "" ? var.results_bucket_name : "${local.name_prefix}-results-${local.account_id}"
}

# ---------------------------------------------------------------------------------------------------------------------
# IAM MODULE - Roles and Policies
# ---------------------------------------------------------------------------------------------------------------------

module "iam" {
  source = "./modules/iam"

  project_name       = var.project_name
  environment        = var.environment
  raw_bucket_arn     = module.s3.raw_bucket_arn
  processed_bucket_arn = module.s3.processed_bucket_arn
  results_bucket_arn = module.s3.results_bucket_arn
  glue_database_name = var.glue_database_name
  enable_lakeformation = var.enable_lakeformation
}

# ---------------------------------------------------------------------------------------------------------------------
# S3 MODULE - Data Lake Storage
# ---------------------------------------------------------------------------------------------------------------------

module "s3" {
  source = "./modules/s3"

  project_name          = var.project_name
  environment           = var.environment
  raw_bucket_name       = local.raw_bucket_name
  processed_bucket_name = local.processed_bucket_name
  results_bucket_name   = local.results_bucket_name
}

# ---------------------------------------------------------------------------------------------------------------------
# GLUE MODULE - Data Catalog and ETL
# ---------------------------------------------------------------------------------------------------------------------

module "glue" {
  source = "./modules/glue"

  project_name           = var.project_name
  environment            = var.environment
  database_name          = var.glue_database_name
  etl_job_name           = var.glue_etl_job_name
  crawler_name           = var.glue_crawler_name
  glue_role_arn          = module.iam.glue_role_arn
  raw_bucket_name        = module.s3.raw_bucket_name
  processed_bucket_name  = module.s3.processed_bucket_name
  etl_script_bucket      = module.s3.results_bucket_name
  worker_type            = var.glue_worker_type
  number_of_workers      = var.glue_number_of_workers
}

# ---------------------------------------------------------------------------------------------------------------------
# ATHENA MODULE - Query Engine
# ---------------------------------------------------------------------------------------------------------------------

module "athena" {
  source = "./modules/athena"

  project_name            = var.project_name
  environment             = var.environment
  workgroup_name          = var.athena_workgroup_name
  results_bucket_name     = module.s3.results_bucket_name
  database_name           = var.glue_database_name
  query_timeout           = var.athena_query_timeout
  bytes_scanned_cutoff    = var.athena_bytes_scanned_cutoff
}

# ---------------------------------------------------------------------------------------------------------------------
# LAKE FORMATION MODULE - Data Governance
# ---------------------------------------------------------------------------------------------------------------------

module "lakeformation" {
  source = "./modules/lakeformation"
  count  = var.enable_lakeformation ? 1 : 0

  project_name         = var.project_name
  environment          = var.environment
  admin_arns           = var.lakeformation_admin_arns
  raw_bucket_arn       = module.s3.raw_bucket_arn
  processed_bucket_arn = module.s3.processed_bucket_arn
  database_name        = var.glue_database_name
  glue_role_arn        = module.iam.glue_role_arn
  lambda_role_arn      = module.iam.lambda_role_arn
  lakeformation_role_arn = module.iam.lakeformation_role_arn
}

# ---------------------------------------------------------------------------------------------------------------------
# LAMBDA MODULE - Serverless Functions
# ---------------------------------------------------------------------------------------------------------------------

module "lambda" {
  source = "./modules/lambda"

  project_name       = var.project_name
  environment        = var.environment
  lambda_role_arn    = module.iam.lambda_role_arn
  memory_size        = var.lambda_memory_size
  timeout            = var.lambda_timeout
  runtime            = var.lambda_runtime
  raw_bucket_name    = module.s3.raw_bucket_name
  processed_bucket_name = module.s3.processed_bucket_name
  results_bucket_name = module.s3.results_bucket_name
  glue_database      = var.glue_database_name
  athena_workgroup   = var.athena_workgroup_name
  glue_etl_job_name  = var.glue_etl_job_name
  glue_crawler_name  = var.glue_crawler_name
}

# ---------------------------------------------------------------------------------------------------------------------
# EVENTBRIDGE MODULE - Scheduled ETL
# ---------------------------------------------------------------------------------------------------------------------

module "eventbridge" {
  source = "./modules/eventbridge"
  count  = var.enable_scheduled_etl ? 1 : 0

  project_name        = var.project_name
  environment         = var.environment
  schedule_expression = var.etl_schedule_expression
  etl_lambda_arn      = module.lambda.etl_function_arn
  etl_lambda_name     = module.lambda.etl_function_name
}

# ---------------------------------------------------------------------------------------------------------------------
# CLOUDWATCH MODULE - Monitoring and Logging
# ---------------------------------------------------------------------------------------------------------------------

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name      = var.project_name
  environment       = var.environment
  lambda_functions  = module.lambda.function_names
  glue_job_name     = var.glue_etl_job_name
  athena_workgroup  = var.athena_workgroup_name
}
