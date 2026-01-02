# =============================================================================
# AWS ML Platform - Main Terraform Configuration
# =============================================================================

locals {
  project_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }

  # Lambda environment variables
  lambda_env_vars = {
    AWS_REGION               = var.aws_region
    DOCUMENTS_TABLE          = module.dynamodb.documents_table_name
    RAW_BUCKET               = module.s3.raw_bucket_name
    PROCESSED_BUCKET         = module.s3.processed_bucket_name
    MODEL_BUCKET             = module.s3.model_bucket_name
    PROCESSING_QUEUE_URL     = module.sqs.processing_queue_url
    SUCCESS_TOPIC_ARN        = module.sns.success_topic_arn
    FAILURE_TOPIC_ARN        = module.sns.failure_topic_arn
    ALERT_TOPIC_ARN          = module.sns.alert_topic_arn
    WORKFLOW_ARN             = module.step_functions.document_workflow_arn
    BEDROCK_MODEL_ID         = var.bedrock_model_id
    BEDROCK_MAX_TOKENS       = tostring(var.bedrock_max_tokens)
    ENABLE_PII_DETECTION     = tostring(var.enable_pii_detection)
    ENABLE_MODERATION        = tostring(var.enable_moderation)
    ENABLE_SUMMARIZATION     = tostring(var.enable_summarization)
    ENABLE_QA_GENERATION     = tostring(var.enable_qa_generation)
    POWERTOOLS_SERVICE_NAME  = var.project_name
    LOG_LEVEL                = "INFO"
  }
}

# =============================================================================
# S3 Buckets
# =============================================================================

module "s3" {
  source = "./modules/s3"

  project_prefix        = local.project_prefix
  raw_bucket_name       = var.raw_bucket_name
  processed_bucket_name = var.processed_bucket_name
  model_bucket_name     = var.model_bucket_name

  tags = local.common_tags
}

# =============================================================================
# DynamoDB Tables
# =============================================================================

module "dynamodb" {
  source = "./modules/dynamodb"

  project_prefix = local.project_prefix
  billing_mode   = var.dynamodb_billing_mode
  read_capacity  = var.dynamodb_read_capacity
  write_capacity = var.dynamodb_write_capacity

  tags = local.common_tags
}

# =============================================================================
# SQS Queues
# =============================================================================

module "sqs" {
  source = "./modules/sqs"

  project_prefix     = local.project_prefix
  visibility_timeout = var.sqs_visibility_timeout
  message_retention  = var.sqs_message_retention
  max_receive_count  = var.sqs_max_receive_count

  tags = local.common_tags
}

# =============================================================================
# SNS Topics
# =============================================================================

module "sns" {
  source = "./modules/sns"

  project_prefix            = local.project_prefix
  notification_email        = var.notification_email
  enable_email_notifications = var.enable_email_notifications

  tags = local.common_tags
}

# =============================================================================
# IAM Roles
# =============================================================================

module "lambda_iam" {
  source = "./modules/iam/lambda"

  project_prefix     = local.project_prefix
  raw_bucket_arn     = module.s3.raw_bucket_arn
  processed_bucket_arn = module.s3.processed_bucket_arn
  model_bucket_arn   = module.s3.model_bucket_arn
  documents_table_arn = module.dynamodb.documents_table_arn
  processing_queue_arn = module.sqs.processing_queue_arn
  dlq_arn            = module.sqs.dlq_arn
  success_topic_arn  = module.sns.success_topic_arn
  failure_topic_arn  = module.sns.failure_topic_arn
  alert_topic_arn    = module.sns.alert_topic_arn
  workflow_arn       = module.step_functions.document_workflow_arn

  tags = local.common_tags
}

module "sagemaker_iam" {
  source = "./modules/iam/sagemaker"

  project_prefix       = local.project_prefix
  model_bucket_arn     = module.s3.model_bucket_arn
  processed_bucket_arn = module.s3.processed_bucket_arn

  tags = local.common_tags
}

# =============================================================================
# Lambda Functions
# =============================================================================

# Document Ingestion
module "lambda_ingestion" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-document-ingestion"
  description   = "Ingests documents from S3 and starts processing workflow"
  handler       = "src.handlers.document_ingestion.handler"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = local.lambda_env_vars

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# Text Extraction
module "lambda_extraction" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-text-extraction"
  description   = "Extracts text using Amazon Textract"
  handler       = "src.handlers.text_extraction.handler"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_size
  timeout       = 300 # Textract may take longer

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = local.lambda_env_vars

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# Audio Transcription
module "lambda_transcription" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-audio-transcription"
  description   = "Transcribes audio using Amazon Transcribe"
  handler       = "src.handlers.audio_transcription.handler"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_size
  timeout       = 300

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = local.lambda_env_vars

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# Content Analysis
module "lambda_analysis" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-content-analysis"
  description   = "Analyzes content using Comprehend and Rekognition"
  handler       = "src.handlers.content_analysis.handler"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = local.lambda_env_vars

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# SageMaker Inference
module "lambda_inference" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-sagemaker-inference"
  description   = "Classifies documents using SageMaker endpoint"
  handler       = "src.handlers.sagemaker_inference.handler"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = merge(local.lambda_env_vars, {
    SAGEMAKER_ENDPOINT_NAME = var.create_sagemaker_endpoint ? module.sagemaker[0].endpoint_name : ""
  })

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# Bedrock Generation
module "lambda_bedrock" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-bedrock-generation"
  description   = "Generates summaries and Q&A using Amazon Bedrock"
  handler       = "src.handlers.bedrock_generation.handler"
  runtime       = var.lambda_runtime
  memory_size   = 1024 # More memory for Bedrock
  timeout       = 120

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = local.lambda_env_vars

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# Workflow Orchestration
module "lambda_workflow" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-workflow-orchestration"
  description   = "Handles workflow routing and finalization"
  handler       = "src.handlers.workflow_orchestration.handler"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_size
  timeout       = var.lambda_timeout

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = local.lambda_env_vars

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# Training Pipeline
module "lambda_training" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-training-pipeline"
  description   = "Manages SageMaker training jobs"
  handler       = "src.handlers.training_pipeline.handler"
  runtime       = var.lambda_runtime
  memory_size   = var.lambda_memory_size
  timeout       = 300

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = merge(local.lambda_env_vars, {
    SAGEMAKER_ROLE_ARN     = module.sagemaker_iam.role_arn
    TRAINING_INSTANCE_TYPE = var.training_instance_type
    ENDPOINT_INSTANCE_TYPE = var.sagemaker_endpoint_instance_type
  })

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# Notification
module "lambda_notification" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-notification"
  description   = "Handles SNS notifications"
  handler       = "src.handlers.notification.handler"
  runtime       = var.lambda_runtime
  memory_size   = 256
  timeout       = 30

  source_path   = var.lambda_package_path
  role_arn      = module.lambda_iam.role_arn

  environment_variables = local.lambda_env_vars

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# =============================================================================
# S3 Event Trigger
# =============================================================================

resource "aws_lambda_permission" "s3_ingestion" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_ingestion.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = module.s3.raw_bucket_arn
}

resource "aws_s3_bucket_notification" "raw_bucket" {
  bucket = module.s3.raw_bucket_name

  lambda_function {
    lambda_function_arn = module.lambda_ingestion.function_arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "input/"
  }

  depends_on = [aws_lambda_permission.s3_ingestion]
}

# =============================================================================
# Step Functions
# =============================================================================

module "step_functions" {
  source = "./modules/step-functions"

  project_prefix = local.project_prefix

  # Lambda function ARNs
  validate_lambda_arn     = module.lambda_workflow.function_arn
  route_lambda_arn        = module.lambda_workflow.function_arn
  extraction_lambda_arn   = module.lambda_extraction.function_arn
  transcription_lambda_arn = module.lambda_transcription.function_arn
  analysis_lambda_arn     = module.lambda_analysis.function_arn
  inference_lambda_arn    = module.lambda_inference.function_arn
  bedrock_lambda_arn      = module.lambda_bedrock.function_arn
  finalize_lambda_arn     = module.lambda_workflow.function_arn

  # SNS topics
  success_topic_arn = module.sns.success_topic_arn
  failure_topic_arn = module.sns.failure_topic_arn

  log_retention_days = var.lambda_log_retention_days

  tags = local.common_tags
}

# =============================================================================
# API Gateway
# =============================================================================

module "api_gateway" {
  source = "./modules/api-gateway"

  project_prefix = local.project_prefix

  inference_lambda_arn = module.lambda_inference.function_arn
  inference_lambda_name = module.lambda_inference.function_name
  bedrock_lambda_arn   = module.lambda_bedrock.function_arn
  bedrock_lambda_name  = module.lambda_bedrock.function_name

  tags = local.common_tags
}

# =============================================================================
# SageMaker (Optional)
# =============================================================================

module "sagemaker" {
  source = "./modules/sagemaker"
  count  = var.create_sagemaker_endpoint ? 1 : 0

  project_prefix      = local.project_prefix
  model_bucket_name   = module.s3.model_bucket_name
  role_arn            = module.sagemaker_iam.role_arn
  instance_type       = var.sagemaker_endpoint_instance_type
  instance_count      = var.sagemaker_endpoint_instance_count

  tags = local.common_tags
}

# =============================================================================
# CloudWatch Dashboard
# =============================================================================

module "cloudwatch" {
  source = "./modules/cloudwatch"

  project_prefix = local.project_prefix

  lambda_function_names = [
    module.lambda_ingestion.function_name,
    module.lambda_extraction.function_name,
    module.lambda_transcription.function_name,
    module.lambda_analysis.function_name,
    module.lambda_inference.function_name,
    module.lambda_bedrock.function_name,
    module.lambda_workflow.function_name,
    module.lambda_notification.function_name,
  ]

  workflow_name = module.step_functions.document_workflow_name

  tags = local.common_tags
}
