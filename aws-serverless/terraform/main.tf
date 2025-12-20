# =============================================================================
# AWS Serverless Enterprise Platform - Root Module
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# -----------------------------------------------------------------------------
# Local Variables
# -----------------------------------------------------------------------------

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  lambda_env_vars = {
    ENVIRONMENT              = var.environment
    LOG_LEVEL                = var.log_level
    POWERTOOLS_SERVICE_NAME  = var.project_name
    AWS_REGION               = var.aws_region
    COGNITO_USER_POOL_ID     = var.enable_cognito ? module.cognito[0].user_pool_id : ""
    COGNITO_CLIENT_ID        = var.enable_cognito ? module.cognito[0].client_id : ""
    COGNITO_REGION           = var.aws_region
    TENANT_TABLE             = module.dynamodb.table_name
    AUDIT_TABLE              = var.enable_audit_logging ? module.dynamodb_audit[0].table_name : ""
    PROCESSING_QUEUE_URL     = module.sqs.queue_url
    DLQ_URL                  = module.sqs.dlq_url
    NOTIFICATION_TOPIC_ARN   = module.sns.notification_topic_arn
    ALERT_TOPIC_ARN          = module.sns.alert_topic_arn
    EVENT_BUS_NAME           = module.eventbridge.event_bus_name
    KMS_KEY_ID               = var.enable_encryption ? module.kms[0].key_id : ""
    ENABLE_AUDIT_LOGGING     = tostring(var.enable_audit_logging)
    ENABLE_REQUEST_VALIDATION = tostring(var.enable_request_validation)
  }
}

# -----------------------------------------------------------------------------
# KMS Encryption Key
# -----------------------------------------------------------------------------

module "kms" {
  count  = var.enable_encryption ? 1 : 0
  source = "./modules/kms"

  name_prefix        = local.name_prefix
  enable_key_rotation = true
  allow_aws_services  = true
  tags               = local.common_tags
}

# -----------------------------------------------------------------------------
# VPC (Optional - for private Lambda deployment)
# -----------------------------------------------------------------------------

module "vpc" {
  count  = var.enable_vpc ? 1 : 0
  source = "./modules/vpc"

  name_prefix        = local.name_prefix
  vpc_cidr           = var.vpc_cidr
  az_count           = var.multi_az ? 3 : 2
  enable_nat_gateway = var.enable_nat_gateway
  single_nat_gateway = !var.multi_az
  enable_flow_logs   = var.enable_flow_logs
  tags               = local.common_tags
}

module "security_groups" {
  count  = var.enable_vpc ? 1 : 0
  source = "./modules/security-groups"

  name_prefix       = local.name_prefix
  vpc_id            = module.vpc[0].vpc_id
  vpc_cidr          = var.vpc_cidr
  create_database_sg = var.create_database_resources
  create_cache_sg    = var.create_cache_resources
  tags              = local.common_tags
}

# -----------------------------------------------------------------------------
# Cognito Authentication
# -----------------------------------------------------------------------------

module "cognito" {
  count  = var.enable_cognito ? 1 : 0
  source = "./modules/cognito"

  name_prefix             = local.name_prefix
  app_name                = var.project_name
  password_min_length     = var.password_min_length
  mfa_configuration       = var.mfa_configuration
  advanced_security_mode  = var.environment == "prod" ? "ENFORCED" : "AUDIT"
  callback_urls           = var.cognito_callback_urls
  logout_urls             = var.cognito_logout_urls
  create_identity_pool    = false
  tags                    = local.common_tags
}

# -----------------------------------------------------------------------------
# DynamoDB Tables
# -----------------------------------------------------------------------------

module "dynamodb" {
  source = "./modules/dynamodb"

  name_prefix    = local.name_prefix
  table_name     = "tenants"
  hash_key       = "PK"
  range_key      = "SK"
  billing_mode   = var.dynamodb_billing_mode
  enable_pitr    = var.environment == "prod"
  enable_ttl     = true
  ttl_attribute  = "ttl"
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  global_secondary_indexes = [
    {
      name      = "GSI1"
      hash_key  = "GSI1PK"
      range_key = "GSI1SK"
    }
  ]

  tags = local.common_tags
}

module "dynamodb_audit" {
  count  = var.enable_audit_logging ? 1 : 0
  source = "./modules/dynamodb"

  name_prefix    = local.name_prefix
  table_name     = "audit"
  hash_key       = "PK"
  range_key      = "SK"
  billing_mode   = var.dynamodb_billing_mode
  enable_pitr    = var.environment == "prod"
  enable_ttl     = true
  ttl_attribute  = "ttl"
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  global_secondary_indexes = [
    {
      name      = "GSI1"
      hash_key  = "GSI1PK"
      range_key = "GSI1SK"
    },
    {
      name      = "GSI2"
      hash_key  = "GSI2PK"
      range_key = "GSI2SK"
    }
  ]

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# SQS Queues
# -----------------------------------------------------------------------------

module "sqs" {
  source = "./modules/sqs"

  name_prefix            = local.name_prefix
  visibility_timeout     = 120
  message_retention      = 1209600  # 14 days
  max_receive_count      = 3
  enable_encryption      = var.enable_encryption
  kms_key_id             = var.enable_encryption ? module.kms[0].key_id : null
  tags                   = local.common_tags
}

# -----------------------------------------------------------------------------
# SNS Topics
# -----------------------------------------------------------------------------

module "sns" {
  source = "./modules/sns"

  name_prefix        = local.name_prefix
  enable_encryption  = var.enable_encryption
  kms_key_id         = var.enable_encryption ? module.kms[0].key_id : null
  notification_email = var.notification_email
  tags               = local.common_tags
}

# -----------------------------------------------------------------------------
# EventBridge
# -----------------------------------------------------------------------------

module "eventbridge" {
  source = "./modules/eventbridge"

  name_prefix = local.name_prefix
  tags        = local.common_tags
}

# -----------------------------------------------------------------------------
# CloudWatch Monitoring
# -----------------------------------------------------------------------------

module "cloudwatch" {
  source = "./modules/cloudwatch"

  name_prefix           = local.name_prefix
  log_retention_days    = var.log_retention_days
  alarm_sns_topic_arns  = [module.sns.alert_topic_arn]
  tags                  = local.common_tags
}

# -----------------------------------------------------------------------------
# IAM Roles and Policies (Multi-Tenant)
# -----------------------------------------------------------------------------

module "iam" {
  source = "./modules/iam"

  project_name   = var.project_name
  environment    = var.environment
  aws_region     = var.aws_region
  aws_account_id = data.aws_caller_identity.current.account_id

  enable_permission_boundary = var.environment == "prod"
  allowed_regions            = [var.aws_region]

  kms_key_arn         = var.enable_encryption ? module.kms[0].key_arn : null
  dynamodb_table_arns = [module.dynamodb.table_arn]
  sqs_queue_arns      = [module.sqs.queue_arn, module.sqs.dlq_arn]
  sns_topic_arns      = [module.sns.notification_topic_arn, module.sns.alert_topic_arn]

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Secrets Manager
# -----------------------------------------------------------------------------

module "secrets_manager" {
  source = "./modules/secrets-manager"

  project_name = var.project_name
  environment  = var.environment
  kms_key_arn  = var.enable_encryption ? module.kms[0].key_arn : null

  tenant_secrets = {
    crm_oauth = {
      description = "CRM OAuth credentials template"
      template = {
        client_id     = ""
        client_secret = ""
        redirect_uri  = ""
      }
    }
    email_oauth = {
      description = "Email OAuth credentials template"
      template = {
        client_id     = ""
        client_secret = ""
        tenant_id     = ""
      }
    }
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# VPC Endpoints (Private AWS Service Access)
# -----------------------------------------------------------------------------

module "vpc_endpoints" {
  count  = var.enable_vpc ? 1 : 0
  source = "./modules/vpc-endpoints"

  project_name      = var.project_name
  environment       = var.environment
  vpc_id            = module.vpc[0].vpc_id
  aws_region        = var.aws_region
  subnet_ids        = module.vpc[0].private_subnet_ids
  security_group_id = module.security_groups[0].vpc_endpoint_sg_id
  route_table_ids   = module.vpc[0].private_route_table_ids

  # Gateway endpoints (free)
  enable_s3_endpoint       = true
  enable_dynamodb_endpoint = true

  # Interface endpoints (charged)
  enable_secrets_manager_endpoint = true
  enable_ssm_endpoint             = true
  enable_sqs_endpoint             = true
  enable_sns_endpoint             = true
  enable_kms_endpoint             = var.enable_encryption
  enable_logs_endpoint            = true
  enable_events_endpoint          = true
  enable_bedrock_endpoint         = true  # For GenAI

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# WAF (Web Application Firewall)
# -----------------------------------------------------------------------------

module "waf" {
  count  = var.enable_waf ? 1 : 0
  source = "./modules/waf"

  project_name   = var.project_name
  environment    = var.environment
  scope          = "REGIONAL"

  rate_limit        = var.waf_rate_limit
  rate_limit_action = "block"

  # Managed Rules
  enable_common_rules     = true
  enable_sqli_rules       = true
  enable_xss_rules        = true
  enable_known_bad_inputs = true
  enable_ip_reputation    = true
  enable_anonymous_ip     = var.environment == "prod"
  enable_bot_control      = false  # Additional cost

  # Logging
  enable_logging     = true
  log_retention_days = var.log_retention_days

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# CloudTrail (Audit Logging)
# -----------------------------------------------------------------------------

module "cloudtrail" {
  count  = var.enable_audit_logging ? 1 : 0
  source = "./modules/cloudtrail"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = data.aws_caller_identity.current.account_id
  aws_region     = var.aws_region
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  is_multi_region               = var.environment == "prod"
  enable_log_file_validation    = true
  include_global_service_events = true

  enable_cloudwatch_logs        = true
  cloudwatch_log_retention_days = var.log_retention_days
  log_retention_days            = 90

  enable_management_events    = true
  management_event_read_write = var.environment == "prod" ? "All" : "WriteOnly"
  enable_data_events          = var.environment == "prod"
  enable_insights             = var.environment == "prod"

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# AWS Config (Compliance Monitoring)
# -----------------------------------------------------------------------------

module "config" {
  count  = var.enable_config ? 1 : 0
  source = "./modules/config"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = data.aws_caller_identity.current.account_id
  aws_region     = var.aws_region

  recording_enabled        = true
  all_supported            = true
  include_global_resources = true
  log_retention_days       = 90

  # Compliance Rules
  enable_encrypted_volumes    = true
  enable_s3_bucket_encryption = true
  enable_root_mfa             = true
  enable_iam_password_policy  = true
  enable_cloudtrail_enabled   = true

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# AWS Budgets (Cost Management)
# -----------------------------------------------------------------------------

module "budgets" {
  source = "./modules/budgets"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = data.aws_caller_identity.current.account_id

  budget_limit       = var.budget_limit
  notification_email = var.notification_email

  notification_threshold_50       = true
  notification_threshold_80       = true
  notification_threshold_100      = true
  notification_threshold_forecast = true

  enable_lambda_budget     = true
  lambda_budget_limit      = var.budget_limit * 0.3
  enable_dynamodb_budget   = true
  dynamodb_budget_limit    = var.budget_limit * 0.2
  enable_api_gateway_budget = true
  api_gateway_budget_limit  = var.budget_limit * 0.1

  cost_allocation_tag = "Project"

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

data "aws_region" "current" {}

# -----------------------------------------------------------------------------
# Additional DynamoDB Tables for Multi-Tenant SaaS
# -----------------------------------------------------------------------------

# Email Connections Table
module "dynamodb_email_connections" {
  source = "./modules/dynamodb"

  name_prefix    = local.name_prefix
  table_name     = "email-connections"
  hash_key       = "pk"
  range_key      = "sk"
  billing_mode   = var.dynamodb_billing_mode
  enable_pitr    = var.environment == "prod"
  enable_ttl     = false
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  global_secondary_indexes = [
    {
      name      = "status-index"
      hash_key  = "tenant_id"
      range_key = "status"
    }
  ]

  tags = local.common_tags
}

# Email Messages Table
module "dynamodb_email_messages" {
  source = "./modules/dynamodb"

  name_prefix    = local.name_prefix
  table_name     = "email-messages"
  hash_key       = "pk"
  range_key      = "sk"
  billing_mode   = var.dynamodb_billing_mode
  enable_pitr    = var.environment == "prod"
  enable_ttl     = true
  ttl_attribute  = "ttl"
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  global_secondary_indexes = [
    {
      name      = "connection-index"
      hash_key  = "connection_id"
      range_key = "received_at"
    }
  ]

  tags = local.common_tags
}

# CRM Connections Table
module "dynamodb_crm_connections" {
  source = "./modules/dynamodb"

  name_prefix    = local.name_prefix
  table_name     = "crm-connections"
  hash_key       = "pk"
  range_key      = "sk"
  billing_mode   = var.dynamodb_billing_mode
  enable_pitr    = var.environment == "prod"
  enable_ttl     = false
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  tags = local.common_tags
}

# CRM Contacts Table
module "dynamodb_crm_contacts" {
  source = "./modules/dynamodb"

  name_prefix    = local.name_prefix
  table_name     = "crm-contacts"
  hash_key       = "pk"
  range_key      = "sk"
  billing_mode   = var.dynamodb_billing_mode
  enable_pitr    = var.environment == "prod"
  enable_ttl     = false
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  global_secondary_indexes = [
    {
      name      = "email-index"
      hash_key  = "tenant_id"
      range_key = "email"
    },
    {
      name      = "connection-index"
      hash_key  = "connection_id"
      range_key = "synced_at"
    }
  ]

  tags = local.common_tags
}

# CRM Deals Table
module "dynamodb_crm_deals" {
  source = "./modules/dynamodb"

  name_prefix    = local.name_prefix
  table_name     = "crm-deals"
  hash_key       = "pk"
  range_key      = "sk"
  billing_mode   = var.dynamodb_billing_mode
  enable_pitr    = var.environment == "prod"
  enable_ttl     = false
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  global_secondary_indexes = [
    {
      name      = "stage-index"
      hash_key  = "tenant_id"
      range_key = "stage"
    }
  ]

  tags = local.common_tags
}

# CRM Activities Table
module "dynamodb_crm_activities" {
  source = "./modules/dynamodb"

  name_prefix    = local.name_prefix
  table_name     = "crm-activities"
  hash_key       = "pk"
  range_key      = "sk"
  billing_mode   = var.dynamodb_billing_mode
  enable_pitr    = var.environment == "prod"
  enable_ttl     = true
  ttl_attribute  = "ttl"
  kms_key_arn    = var.enable_encryption ? module.kms[0].key_arn : null

  global_secondary_indexes = [
    {
      name      = "contact-index"
      hash_key  = "tenant_id"
      range_key = "created_at"
    }
  ]

  tags = local.common_tags
}
