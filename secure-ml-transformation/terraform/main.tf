################################################################################
# Secure ML Data Transformation Pipeline - Terraform Configuration
################################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Uncomment and configure for remote state
  # backend "s3" {
  #   bucket         = "terraform-state-bucket"
  #   key            = "secure-ml-transform/terraform.tfstate"
  #   region         = "eu-central-2"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

################################################################################
# Local Values
################################################################################

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }
}

################################################################################
# KMS Module
################################################################################

module "kms" {
  source = "./modules/kms"

  project_name = var.project_name
  environment  = var.environment
  name_prefix  = local.name_prefix
}

################################################################################
# VPC Module
################################################################################

module "vpc" {
  source = "./modules/vpc"

  project_name         = var.project_name
  environment          = var.environment
  name_prefix          = local.name_prefix
  vpc_cidr             = var.vpc_cidr
  private_subnet_cidrs = var.private_subnet_cidrs
  availability_zones   = var.availability_zones
}

################################################################################
# S3 Module
################################################################################

module "s3" {
  source = "./modules/s3"

  project_name = var.project_name
  environment  = var.environment
  name_prefix  = local.name_prefix
  kms_key_arn  = module.kms.key_arn
}

################################################################################
# IAM Module
################################################################################

module "iam" {
  source = "./modules/iam"

  project_name            = var.project_name
  environment             = var.environment
  name_prefix             = local.name_prefix
  raw_data_bucket_arn     = module.s3.raw_data_bucket_arn
  processed_data_bucket_arn = module.s3.processed_data_bucket_arn
  scripts_bucket_arn      = module.s3.scripts_bucket_arn
  kms_key_arn             = module.kms.key_arn
}

################################################################################
# CloudWatch Module
################################################################################

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_name       = var.project_name
  environment        = var.environment
  name_prefix        = local.name_prefix
  log_retention_days = var.log_retention_days
  kms_key_arn        = module.kms.key_arn
}

################################################################################
# Glue Module
################################################################################

module "glue" {
  source = "./modules/glue"

  project_name           = var.project_name
  environment            = var.environment
  name_prefix            = local.name_prefix
  vpc_id                 = module.vpc.vpc_id
  private_subnet_ids     = module.vpc.private_subnet_ids
  glue_security_group_id = module.vpc.glue_security_group_id
  glue_role_arn          = module.iam.glue_role_arn
  scripts_bucket         = module.s3.scripts_bucket_name
  raw_data_bucket        = module.s3.raw_data_bucket_name
  processed_data_bucket  = module.s3.processed_data_bucket_name
  kms_key_arn            = module.kms.key_arn
  glue_worker_type       = var.glue_worker_type
  glue_number_of_workers = var.glue_number_of_workers
  glue_job_timeout       = var.glue_job_timeout
}
