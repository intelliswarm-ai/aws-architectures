# =============================================================================
# GenAI Knowledge Assistant - Terraform Main Configuration
# =============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.common_tags
  }
}

# =============================================================================
# Local Variables
# =============================================================================

locals {
  project_prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  })

  lambda_env_vars = {
    ENVIRONMENT                  = var.environment
    AWS_REGION                   = var.aws_region
    LOG_LEVEL                    = var.environment == "prod" ? "INFO" : "DEBUG"
    POWERTOOLS_SERVICE_NAME      = var.project_name
    POWERTOOLS_METRICS_NAMESPACE = "GenAIKnowledgeAssistant"

    # Bedrock Configuration
    BEDROCK_MODEL_ID           = var.bedrock_model_id
    BEDROCK_EMBEDDING_MODEL_ID = var.bedrock_embedding_model_id

    # Storage
    DOCUMENTS_BUCKET  = module.s3.documents_bucket_name
    DOCUMENTS_TABLE   = module.dynamodb.documents_table_name
    CONVERSATIONS_TABLE = module.dynamodb.conversations_table_name

    # OpenSearch
    OPENSEARCH_COLLECTION_ENDPOINT = module.opensearch.collection_endpoint
    OPENSEARCH_COLLECTION_NAME     = var.opensearch_collection_name
    OPENSEARCH_INDEX_NAME          = "knowledge-index"
    OPENSEARCH_VECTOR_DIMENSION    = var.vector_dimension

    # RAG Configuration
    RETRIEVAL_TOP_K         = "5"
    RETRIEVAL_SCORE_THRESHOLD = "0.7"
    CHUNK_SIZE              = tostring(var.chunk_size)
    CHUNK_OVERLAP           = tostring(var.chunk_overlap)
  }

  # Conditionally add Knowledge Base env vars
  kb_env_vars = var.create_knowledge_base ? {
    KNOWLEDGE_BASE_ID             = module.bedrock[0].knowledge_base_id
    KNOWLEDGE_BASE_DATA_SOURCE_ID = module.bedrock[0].data_source_id
  } : {}

  # Conditionally add Agent env vars
  agent_env_vars = var.enable_bedrock_agent ? {
    AGENT_ID       = module.bedrock[0].agent_id
    AGENT_ALIAS_ID = module.bedrock[0].agent_alias_id
    ENABLE_AGENT   = "true"
  } : {
    ENABLE_AGENT = "false"
  }

  all_lambda_env_vars = merge(
    local.lambda_env_vars,
    local.kb_env_vars,
    local.agent_env_vars
  )
}

# =============================================================================
# Data Sources
# =============================================================================

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# =============================================================================
# S3 Module
# =============================================================================

module "s3" {
  source = "./modules/s3"

  project_prefix      = local.project_prefix
  documents_bucket_name = var.documents_bucket_name
  enable_versioning   = var.enable_s3_versioning
  tags                = local.common_tags
}

# =============================================================================
# DynamoDB Module
# =============================================================================

module "dynamodb" {
  source = "./modules/dynamodb"

  project_prefix = local.project_prefix
  environment    = var.environment
  tags           = local.common_tags
}

# =============================================================================
# OpenSearch Serverless Module
# =============================================================================

module "opensearch" {
  source = "./modules/opensearch"

  project_prefix      = local.project_prefix
  collection_name     = var.opensearch_collection_name
  vector_dimension    = var.vector_dimension
  standby_replicas    = var.opensearch_standby_replicas ? "ENABLED" : "DISABLED"
  tags                = local.common_tags
}

# =============================================================================
# IAM Module
# =============================================================================

module "iam" {
  source = "./modules/iam"

  project_prefix              = local.project_prefix
  aws_region                  = var.aws_region
  account_id                  = data.aws_caller_identity.current.account_id
  documents_bucket_arn        = module.s3.documents_bucket_arn
  documents_table_arn         = module.dynamodb.documents_table_arn
  conversations_table_arn     = module.dynamodb.conversations_table_arn
  opensearch_collection_arn   = module.opensearch.collection_arn
  bedrock_model_id            = var.bedrock_model_id
  bedrock_embedding_model_id  = var.bedrock_embedding_model_id
  tags                        = local.common_tags
}

# =============================================================================
# Lambda Module
# =============================================================================

module "lambda" {
  source = "./modules/lambda"

  project_prefix     = local.project_prefix
  lambda_role_arn    = module.iam.lambda_role_arn
  memory_size        = var.lambda_memory_size
  timeout            = var.lambda_timeout
  enable_xray        = var.enable_xray
  log_retention_days = var.lambda_log_retention_days
  environment_variables = local.all_lambda_env_vars
  documents_bucket_arn  = module.s3.documents_bucket_arn
  documents_bucket_name = module.s3.documents_bucket_name
  tags               = local.common_tags
}

# =============================================================================
# API Gateway Module
# =============================================================================

module "api_gateway" {
  source = "./modules/api-gateway"

  project_prefix       = local.project_prefix
  environment          = var.environment
  api_handler_arn      = module.lambda.api_handler_arn
  api_handler_name     = module.lambda.api_handler_name
  agent_handler_arn    = module.lambda.agent_handler_arn
  agent_handler_name   = module.lambda.agent_handler_name
  throttle_rate_limit  = var.api_throttle_rate_limit
  throttle_burst_limit = var.api_throttle_burst_limit
  enable_logging       = var.enable_api_logging
  tags                 = local.common_tags
}

# =============================================================================
# Bedrock Module (Knowledge Base & Agent)
# =============================================================================

module "bedrock" {
  source = "./modules/bedrock"
  count  = var.create_knowledge_base ? 1 : 0

  project_prefix             = local.project_prefix
  environment                = var.environment
  aws_region                 = var.aws_region
  account_id                 = data.aws_caller_identity.current.account_id
  documents_bucket_arn       = module.s3.documents_bucket_arn
  documents_bucket_name      = module.s3.documents_bucket_name
  opensearch_collection_arn  = module.opensearch.collection_arn
  opensearch_collection_endpoint = module.opensearch.collection_endpoint
  embedding_model_id         = var.bedrock_embedding_model_id
  foundation_model_id        = var.bedrock_model_id
  vector_dimension           = var.vector_dimension
  chunk_size                 = var.chunk_size
  chunk_overlap              = var.chunk_overlap
  create_agent               = var.enable_bedrock_agent
  tags                       = local.common_tags
}

# =============================================================================
# CloudWatch Module
# =============================================================================

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_prefix     = local.project_prefix
  environment        = var.environment
  api_gateway_id     = module.api_gateway.api_id
  api_gateway_stage  = module.api_gateway.stage_name
  lambda_functions   = module.lambda.function_names
  tags               = local.common_tags
}
