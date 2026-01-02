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
    tags = {
      Project     = "call-sentiment"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  name_prefix = "call-sentiment-${var.environment}"
  account_id  = data.aws_caller_identity.current.account_id
  region      = data.aws_region.current.name
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"

  environment          = var.environment
  name_prefix          = local.name_prefix
  transcripts_bucket   = "${local.name_prefix}-transcripts"
  output_bucket        = "${local.name_prefix}-output"
  retention_days       = var.retention_days
  enable_versioning    = var.enable_versioning
}

# IAM Roles and Policies
module "iam" {
  source = "./modules/iam"

  environment           = var.environment
  name_prefix           = local.name_prefix
  transcripts_bucket_arn = module.s3.transcripts_bucket_arn
  output_bucket_arn     = module.s3.output_bucket_arn
  opensearch_domain_arn = module.opensearch.domain_arn
}

# OpenSearch Domain
module "opensearch" {
  source = "./modules/opensearch"

  environment      = var.environment
  name_prefix      = local.name_prefix
  domain_name      = "${local.name_prefix}-search"
  instance_type    = var.opensearch_instance_type
  instance_count   = var.opensearch_instance_count
  ebs_volume_size  = var.opensearch_ebs_volume_size
  master_user_name = var.opensearch_master_user
  master_user_password = var.opensearch_master_password
}

# Lambda Functions
module "lambda" {
  source = "./modules/lambda"

  environment                = var.environment
  name_prefix                = local.name_prefix
  lambda_execution_role_arn  = module.iam.lambda_execution_role_arn
  transcripts_bucket         = module.s3.transcripts_bucket_name
  output_bucket              = module.s3.output_bucket_name
  opensearch_endpoint        = module.opensearch.domain_endpoint
  comprehend_role_arn        = module.iam.comprehend_role_arn
  log_retention_days         = var.log_retention_days

  depends_on = [module.iam, module.s3, module.opensearch]
}

# API Gateway
module "api_gateway" {
  source = "./modules/api_gateway"

  environment           = var.environment
  name_prefix           = local.name_prefix
  api_lambda_invoke_arn = module.lambda.api_handler_invoke_arn
  api_lambda_function_name = module.lambda.api_handler_function_name

  depends_on = [module.lambda]
}

# EventBridge Rules
module "eventbridge" {
  source = "./modules/eventbridge"

  environment                    = var.environment
  name_prefix                    = local.name_prefix
  comprehend_handler_arn         = module.lambda.comprehend_handler_arn
  comprehend_handler_function_name = module.lambda.comprehend_handler_function_name

  depends_on = [module.lambda]
}

# CloudWatch Monitoring
module "cloudwatch" {
  source = "./modules/cloudwatch"

  environment           = var.environment
  name_prefix           = local.name_prefix
  opensearch_domain_name = module.opensearch.domain_name
  lambda_function_names = [
    module.lambda.transcript_processor_function_name,
    module.lambda.comprehend_handler_function_name,
    module.lambda.result_indexer_function_name,
    module.lambda.api_handler_function_name,
  ]
  alarm_email = var.alarm_email

  depends_on = [module.lambda, module.opensearch]
}
