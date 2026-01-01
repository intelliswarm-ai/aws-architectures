################################################################################
# Lambda Module - SMS Processing Functions
################################################################################

data "archive_file" "lambda_placeholder" {
  type        = "zip"
  output_path = "${path.module}/placeholder.zip"

  source {
    content  = "# Placeholder for Lambda deployment"
    filename = "placeholder.py"
  }
}

################################################################################
# Event Processor Lambda
################################################################################

resource "aws_lambda_function" "event_processor" {
  function_name = "${var.project_name}-event-processor"
  role          = var.event_processor_role_arn
  handler       = "handlers.sms_event_processor.handler"
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = {
      STREAM_NAME        = var.kinesis_stream_name
      PINPOINT_APP_ID    = var.pinpoint_app_id
      LOG_LEVEL          = "INFO"
      POWERTOOLS_SERVICE_NAME = "sms-event-processor"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

resource "aws_lambda_event_source_mapping" "event_processor" {
  event_source_arn                   = var.kinesis_stream_arn
  function_name                      = aws_lambda_function.event_processor.arn
  starting_position                  = var.consumer_starting_position
  batch_size                         = var.consumer_batch_size
  parallelization_factor             = var.consumer_parallelization
  maximum_batching_window_in_seconds = var.max_batching_window_seconds
  maximum_retry_attempts             = 3

  filter_criteria {
    filter {
      pattern = jsonencode({
        data = {
          event_type = [{ prefix = "_SMS." }]
        }
      })
    }
  }
}

################################################################################
# Response Handler Lambda
################################################################################

resource "aws_lambda_function" "response_handler" {
  function_name = "${var.project_name}-response-handler"
  role          = var.response_handler_role_arn
  handler       = "handlers.response_handler.handler"
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = {
      STREAM_NAME          = var.kinesis_stream_name
      RESPONSES_TABLE      = var.responses_table_name
      SUBSCRIBERS_TABLE    = var.subscribers_table_name
      NOTIFICATIONS_TOPIC  = var.notifications_topic_arn
      PINPOINT_APP_ID      = var.pinpoint_app_id
      LOG_LEVEL            = "INFO"
      POWERTOOLS_SERVICE_NAME = "sms-response-handler"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

resource "aws_lambda_event_source_mapping" "response_handler" {
  event_source_arn                   = var.kinesis_stream_arn
  function_name                      = aws_lambda_function.response_handler.arn
  starting_position                  = var.consumer_starting_position
  batch_size                         = var.consumer_batch_size
  parallelization_factor             = var.consumer_parallelization
  maximum_batching_window_in_seconds = var.max_batching_window_seconds
  maximum_retry_attempts             = 3

  filter_criteria {
    filter {
      pattern = jsonencode({
        data = {
          event_type = [{ prefix = "_SMS.RECEIVED" }]
        }
      })
    }
  }
}

################################################################################
# Analytics Processor Lambda
################################################################################

resource "aws_lambda_function" "analytics_processor" {
  function_name = "${var.project_name}-analytics-processor"
  role          = var.analytics_processor_role_arn
  handler       = "handlers.analytics_processor.handler"
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = {
      STREAM_NAME     = var.kinesis_stream_name
      PINPOINT_APP_ID = var.pinpoint_app_id
      LOG_LEVEL       = "INFO"
      POWERTOOLS_SERVICE_NAME = "sms-analytics-processor"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

resource "aws_lambda_event_source_mapping" "analytics_processor" {
  event_source_arn                   = var.kinesis_stream_arn
  function_name                      = aws_lambda_function.analytics_processor.arn
  starting_position                  = var.consumer_starting_position
  batch_size                         = var.consumer_batch_size
  parallelization_factor             = var.consumer_parallelization
  maximum_batching_window_in_seconds = var.max_batching_window_seconds
  maximum_retry_attempts             = 3
}

################################################################################
# Archive Consumer Lambda
################################################################################

resource "aws_lambda_function" "archive_consumer" {
  function_name = "${var.project_name}-archive-consumer"
  role          = var.archive_consumer_role_arn
  handler       = "handlers.archive_consumer.handler"
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = data.archive_file.lambda_placeholder.output_path
  source_code_hash = data.archive_file.lambda_placeholder.output_base64sha256

  environment {
    variables = {
      STREAM_NAME    = var.kinesis_stream_name
      ARCHIVE_BUCKET = var.archive_bucket_name
      LOG_LEVEL      = "INFO"
      POWERTOOLS_SERVICE_NAME = "sms-archive-consumer"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = var.tags

  lifecycle {
    ignore_changes = [filename, source_code_hash]
  }
}

resource "aws_lambda_event_source_mapping" "archive_consumer" {
  event_source_arn                   = var.kinesis_stream_arn
  function_name                      = aws_lambda_function.archive_consumer.arn
  starting_position                  = var.consumer_starting_position
  batch_size                         = var.consumer_batch_size
  parallelization_factor             = var.consumer_parallelization
  maximum_batching_window_in_seconds = var.max_batching_window_seconds
  maximum_retry_attempts             = 3
}
