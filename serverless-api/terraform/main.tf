locals {
  project_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
  }

  # Lambda JAR paths
  lambda_jars = {
    task_generator  = "${var.lambda_jar_base_path}/task-generator/target/task-generator-1.0.0-SNAPSHOT.jar"
    task_worker     = "${var.lambda_jar_base_path}/task-worker/target/task-worker-1.0.0-SNAPSHOT.jar"
    workflow        = "${var.lambda_jar_base_path}/workflow-lambdas/target/workflow-lambdas-1.0.0-SNAPSHOT.jar"
    notification    = "${var.lambda_jar_base_path}/notification/target/notification-1.0.0-SNAPSHOT.jar"
  }
}

# =============================================================================
# DynamoDB
# =============================================================================
module "dynamodb" {
  source = "./modules/dynamodb"

  table_name   = "${local.project_prefix}-tasks"
  billing_mode = var.dynamodb_billing_mode
  enable_ttl   = true
  enable_pitr  = var.environment == "prod"

  tags = local.common_tags
}

# =============================================================================
# SQS
# =============================================================================
module "sqs" {
  source = "./modules/sqs"

  queue_name         = "${local.project_prefix}-tasks"
  visibility_timeout = var.sqs_visibility_timeout
  message_retention  = var.sqs_message_retention
  max_receive_count  = var.sqs_max_receive_count

  tags = local.common_tags
}

# =============================================================================
# SNS
# =============================================================================
module "sns" {
  source = "./modules/sns"

  topic_prefix        = local.project_prefix
  email_endpoint      = var.enable_email_notifications ? var.notification_email : ""
  lambda_endpoint_arn = module.lambda_notification.function_arn

  tags = local.common_tags
}

# =============================================================================
# Lambda Functions
# =============================================================================

# Task Generator Lambda
module "lambda_task_generator" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-task-generator"
  description   = "Generates tasks on a schedule and publishes to SQS"
  handler       = "ai.intelliswarm.lambda.generator.handler.TaskGeneratorHandler::handleRequest"
  jar_path      = local.lambda_jars.task_generator

  memory_size        = var.lambda_memory_size
  timeout            = var.lambda_timeout
  log_retention_days = var.lambda_log_retention_days
  enable_snapstart   = true
  enable_xray        = true

  environment_variables = {
    TASK_QUEUE_URL = module.sqs.queue_url
  }

  custom_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:SendMessageBatch"
        ]
        Resource = module.sqs.queue_arn
      }
    ]
  })

  tags = local.common_tags
}

# Task Worker Lambda
module "lambda_task_worker" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-task-worker"
  description   = "Processes tasks from SQS queue"
  handler       = "ai.intelliswarm.lambda.worker.handler.TaskWorkerHandler::handleRequest"
  jar_path      = local.lambda_jars.task_worker

  memory_size        = 1024
  timeout            = 60
  log_retention_days = var.lambda_log_retention_days
  enable_snapstart   = true
  enable_xray        = true

  environment_variables = {
    TASK_TABLE_NAME   = module.dynamodb.table_name
    STATE_MACHINE_ARN = module.step_functions.state_machine_arn
  }

  custom_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = module.sqs.queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem"
        ]
        Resource = module.dynamodb.table_arn
      },
      {
        Effect   = "Allow"
        Action   = "states:StartExecution"
        Resource = module.step_functions.state_machine_arn
      }
    ]
  })

  tags = local.common_tags
}

# Validate Task Lambda (Step Functions)
module "lambda_validate_task" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-validate-task"
  description   = "Validates task input for Step Functions workflow"
  handler       = "ai.intelliswarm.lambda.workflow.handler.ValidateTaskHandler::handleRequest"
  jar_path      = local.lambda_jars.workflow

  memory_size        = var.lambda_memory_size
  timeout            = 15
  log_retention_days = var.lambda_log_retention_days
  enable_snapstart   = true
  enable_xray        = true

  tags = local.common_tags
}

# Process Task Lambda (Step Functions)
module "lambda_process_task" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-process-task"
  description   = "Core task processing for Step Functions workflow"
  handler       = "ai.intelliswarm.lambda.workflow.handler.ProcessTaskHandler::handleRequest"
  jar_path      = local.lambda_jars.workflow

  memory_size        = 1024
  timeout            = 60
  log_retention_days = var.lambda_log_retention_days
  enable_snapstart   = true
  enable_xray        = true

  tags = local.common_tags
}

# Finalize Task Lambda (Step Functions)
module "lambda_finalize_task" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-finalize-task"
  description   = "Finalizes task processing and triggers notifications"
  handler       = "ai.intelliswarm.lambda.workflow.handler.FinalizeTaskHandler::handleRequest"
  jar_path      = local.lambda_jars.workflow

  memory_size        = var.lambda_memory_size
  timeout            = 30
  log_retention_days = var.lambda_log_retention_days
  enable_snapstart   = true
  enable_xray        = true

  environment_variables = {
    TASK_TABLE_NAME = module.dynamodb.table_name
  }

  custom_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = module.dynamodb.table_arn
      }
    ]
  })

  tags = local.common_tags
}

# Notification Lambda
module "lambda_notification" {
  source = "./modules/lambda"

  function_name = "${local.project_prefix}-notification"
  description   = "Handles SNS notifications for task events"
  handler       = "ai.intelliswarm.lambda.notification.handler.NotificationHandler::handleRequest"
  jar_path      = local.lambda_jars.notification

  memory_size        = 256
  timeout            = 15
  log_retention_days = var.lambda_log_retention_days
  enable_snapstart   = true
  enable_xray        = true

  environment_variables = {
    NOTIFICATION_EMAIL = var.notification_email
    EMAIL_ENABLED      = tostring(var.enable_email_notifications)
  }

  tags = local.common_tags
}

# Lambda permission for SNS to invoke notification handler
resource "aws_lambda_permission" "sns_invoke_notification" {
  statement_id  = "AllowSNSInvoke"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_notification.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = module.sns.success_topic_arn
}

resource "aws_lambda_permission" "sns_invoke_notification_failure" {
  statement_id  = "AllowSNSInvokeFailure"
  action        = "lambda:InvokeFunction"
  function_name = module.lambda_notification.function_name
  principal     = "sns.amazonaws.com"
  source_arn    = module.sns.failure_topic_arn
}

# =============================================================================
# SQS Lambda Event Source Mapping
# =============================================================================
resource "aws_lambda_event_source_mapping" "sqs_to_worker" {
  event_source_arn                   = module.sqs.queue_arn
  function_name                      = module.lambda_task_worker.function_arn
  batch_size                         = 10
  maximum_batching_window_in_seconds = 5
  enabled                            = true

  # Enable partial batch response
  function_response_types = ["ReportBatchItemFailures"]
}

# =============================================================================
# Step Functions
# =============================================================================
module "step_functions" {
  source = "./modules/step-functions"

  state_machine_name       = "${local.project_prefix}-workflow"
  validate_task_lambda_arn = module.lambda_validate_task.function_arn
  process_task_lambda_arn  = module.lambda_process_task.function_arn
  finalize_task_lambda_arn = module.lambda_finalize_task.function_arn
  success_topic_arn        = module.sns.success_topic_arn
  failure_topic_arn        = module.sns.failure_topic_arn

  log_level          = var.environment == "prod" ? "ERROR" : "ALL"
  log_retention_days = var.lambda_log_retention_days
  enable_xray        = true

  tags = local.common_tags
}

# =============================================================================
# EventBridge
# =============================================================================
module "eventbridge" {
  source = "./modules/eventbridge"

  rule_name            = "${local.project_prefix}-task-generator-schedule"
  description          = "Triggers task generation on a schedule"
  schedule_expression  = var.task_generation_schedule
  lambda_arn           = module.lambda_task_generator.function_arn
  lambda_function_name = module.lambda_task_generator.function_name
  enabled              = true

  tags = local.common_tags
}

# =============================================================================
# CloudWatch Monitoring
# =============================================================================
module "cloudwatch" {
  source = "./modules/cloudwatch"

  dashboard_name = "${local.project_prefix}-dashboard"
  aws_region     = var.aws_region

  lambda_function_names = [
    module.lambda_task_generator.function_name,
    module.lambda_task_worker.function_name,
    module.lambda_validate_task.function_name,
    module.lambda_process_task.function_name,
    module.lambda_finalize_task.function_name,
    module.lambda_notification.function_name
  ]

  queue_name         = module.sqs.queue_name
  dlq_name           = module.sqs.dlq_name
  table_name         = module.dynamodb.table_name
  state_machine_arn  = module.step_functions.state_machine_arn
  state_machine_name = module.step_functions.state_machine_name

  alarm_sns_topic_arns = [module.sns.failure_topic_arn]

  lambda_error_threshold = 5
  queue_depth_threshold  = 100
  sfn_failure_threshold  = 5

  tags = local.common_tags
}
