# ============================================
# AWS Elastic Beanstalk - Hybrid Architecture
# Spring Boot + On-Premises Oracle Database
# ============================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "terraform-state-inventory"
    key            = "elasticbeanstalk/terraform.tfstate"
    region         = "eu-central-2"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "inventory-management"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ============================================
# Data Sources
# ============================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_availability_zones" "available" {
  state = "available"
}

# ============================================
# Modules
# ============================================

module "vpc" {
  source = "./modules/vpc"

  environment           = var.environment
  vpc_cidr              = var.vpc_cidr
  availability_zones    = slice(data.aws_availability_zones.available.names, 0, 2)
  enable_vpn_gateway    = var.enable_vpn_gateway
  customer_gateway_ip   = var.customer_gateway_ip
  on_premises_cidr      = var.on_premises_cidr
}

module "security" {
  source = "./modules/security"

  environment      = var.environment
  vpc_id           = module.vpc.vpc_id
  on_premises_cidr = var.on_premises_cidr
}

module "elasticbeanstalk" {
  source = "./modules/elasticbeanstalk"

  environment         = var.environment
  application_name    = var.application_name
  solution_stack_name = var.solution_stack_name
  instance_type       = var.instance_type
  min_instances       = var.min_instances
  max_instances       = var.max_instances

  vpc_id             = module.vpc.vpc_id
  public_subnet_ids  = module.vpc.public_subnet_ids
  private_subnet_ids = module.vpc.private_subnet_ids
  security_group_id  = module.security.app_security_group_id

  database_url      = var.database_url
  database_username = var.database_username
  database_password = var.database_password

  s3_bucket_reports = module.s3.reports_bucket_name
}

module "s3" {
  source = "./modules/s3"

  environment      = var.environment
  application_name = var.application_name
}

module "cloudwatch" {
  source = "./modules/cloudwatch"

  environment      = var.environment
  application_name = var.application_name
  eb_environment   = module.elasticbeanstalk.environment_name
  alarm_email      = var.alarm_email
}

# ============================================
# Outputs
# ============================================

output "application_url" {
  description = "Elastic Beanstalk application URL"
  value       = module.elasticbeanstalk.application_url
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "vpn_connection_id" {
  description = "VPN Connection ID (if enabled)"
  value       = module.vpc.vpn_connection_id
}

output "reports_bucket" {
  description = "S3 bucket for reports"
  value       = module.s3.reports_bucket_name
}
