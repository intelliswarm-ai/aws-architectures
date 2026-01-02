################################################################################
# Lambda Functions Module
################################################################################

# Package the Lambda code
data "archive_file" "lambda_package" {
  type        = "zip"
  source_dir  = "${path.module}/../../../src"
  output_path = "${path.module}/../../../dist/lambda.zip"
}

################################################################################
# Lambda Layer for Dependencies
################################################################################

resource "aws_lambda_layer_version" "dependencies" {
  count = var.create_layer ? 1 : 0

  filename            = var.layer_zip_path
  layer_name          = "${var.project_name}-dependencies"
  compatible_runtimes = [var.runtime]

  description = "Dependencies for GPS tracking Lambda functions"
}

################################################################################
# GPS Producer Lambda
################################################################################

resource "aws_lambda_function" "producer" {
  function_name = "${var.project_name}-gps-producer"
  role          = var.producer_role_arn
  handler       = "handlers.gps_producer.handler"
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  layers = var.create_layer ? [aws_lambda_layer_version.dependencies[0].arn] : []

  environment {
    variables = {
      STREAM_NAME   = var.kinesis_stream_name
      STREAM_ARN    = var.kinesis_stream_arn
      NUM_TRUCKS    = var.num_trucks
      BATCH_SIZE    = var.batch_size
      LOG_LEVEL     = var.log_level
      ENVIRONMENT   = var.environment
      POWERTOOLS_SERVICE_NAME = "gps-producer"
      POWERTOOLS_METRICS_NAMESPACE = "GPSTracking"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = merge(var.tags, {
    Name     = "${var.project_name}-gps-producer"
    Function = "producer"
  })
}

resource "aws_cloudwatch_log_group" "producer" {
  name              = "/aws/lambda/${aws_lambda_function.producer.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

################################################################################
# Dashboard Consumer Lambda
################################################################################

resource "aws_lambda_function" "dashboard_consumer" {
  function_name = "${var.project_name}-dashboard-consumer"
  role          = var.dashboard_consumer_role_arn
  handler       = "handlers.dashboard_consumer.handler"
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  layers = var.create_layer ? [aws_lambda_layer_version.dependencies[0].arn] : []

  environment {
    variables = {
      STREAM_NAME    = var.kinesis_stream_name
      DYNAMODB_TABLE = var.positions_table_name
      LOG_LEVEL      = var.log_level
      ENVIRONMENT    = var.environment
      POWERTOOLS_SERVICE_NAME = "dashboard-consumer"
      POWERTOOLS_METRICS_NAMESPACE = "GPSTracking"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = merge(var.tags, {
    Name     = "${var.project_name}-dashboard-consumer"
    Function = "consumer"
  })
}

resource "aws_cloudwatch_log_group" "dashboard_consumer" {
  name              = "/aws/lambda/${aws_lambda_function.dashboard_consumer.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Kinesis Event Source Mapping for Dashboard Consumer
resource "aws_lambda_event_source_mapping" "dashboard_consumer" {
  event_source_arn                   = var.kinesis_stream_arn
  function_name                      = aws_lambda_function.dashboard_consumer.arn
  starting_position                  = var.consumer_starting_position
  batch_size                         = var.consumer_batch_size
  parallelization_factor             = var.consumer_parallelization
  maximum_batching_window_in_seconds = var.max_batching_window_seconds

  # Enable bisect on error for better error handling
  bisect_batch_on_function_error = true

  # Retry configuration
  maximum_retry_attempts = 3
  maximum_record_age_in_seconds = 3600

  # Destination for failed records (optional)
  # destination_config {
  #   on_failure {
  #     destination_arn = var.dlq_arn
  #   }
  # }
}

################################################################################
# Geofence Consumer Lambda
################################################################################

resource "aws_lambda_function" "geofence_consumer" {
  function_name = "${var.project_name}-geofence-consumer"
  role          = var.geofence_consumer_role_arn
  handler       = "handlers.geofence_consumer.handler"
  runtime       = var.runtime
  memory_size   = var.memory_size
  timeout       = var.timeout

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  layers = var.create_layer ? [aws_lambda_layer_version.dependencies[0].arn] : []

  environment {
    variables = {
      STREAM_NAME     = var.kinesis_stream_name
      GEOFENCES_TABLE = var.geofences_table_name
      SNS_TOPIC_ARN   = var.alerts_topic_arn
      LOG_LEVEL       = var.log_level
      ENVIRONMENT     = var.environment
      POWERTOOLS_SERVICE_NAME = "geofence-consumer"
      POWERTOOLS_METRICS_NAMESPACE = "GPSTracking"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = merge(var.tags, {
    Name     = "${var.project_name}-geofence-consumer"
    Function = "consumer"
  })
}

resource "aws_cloudwatch_log_group" "geofence_consumer" {
  name              = "/aws/lambda/${aws_lambda_function.geofence_consumer.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Kinesis Event Source Mapping for Geofence Consumer
resource "aws_lambda_event_source_mapping" "geofence_consumer" {
  event_source_arn                   = var.kinesis_stream_arn
  function_name                      = aws_lambda_function.geofence_consumer.arn
  starting_position                  = var.consumer_starting_position
  batch_size                         = var.consumer_batch_size
  parallelization_factor             = var.consumer_parallelization
  maximum_batching_window_in_seconds = var.max_batching_window_seconds

  bisect_batch_on_function_error = true
  maximum_retry_attempts = 3
  maximum_record_age_in_seconds = 3600
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

  filename         = data.archive_file.lambda_package.output_path
  source_code_hash = data.archive_file.lambda_package.output_base64sha256

  layers = var.create_layer ? [aws_lambda_layer_version.dependencies[0].arn] : []

  environment {
    variables = {
      STREAM_NAME = var.kinesis_stream_name
      S3_BUCKET   = var.archive_bucket_name
      LOG_LEVEL   = var.log_level
      ENVIRONMENT = var.environment
      POWERTOOLS_SERVICE_NAME = "archive-consumer"
      POWERTOOLS_METRICS_NAMESPACE = "GPSTracking"
    }
  }

  tracing_config {
    mode = "Active"
  }

  tags = merge(var.tags, {
    Name     = "${var.project_name}-archive-consumer"
    Function = "consumer"
  })
}

resource "aws_cloudwatch_log_group" "archive_consumer" {
  name              = "/aws/lambda/${aws_lambda_function.archive_consumer.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# Kinesis Event Source Mapping for Archive Consumer
resource "aws_lambda_event_source_mapping" "archive_consumer" {
  event_source_arn                   = var.kinesis_stream_arn
  function_name                      = aws_lambda_function.archive_consumer.arn
  starting_position                  = var.consumer_starting_position
  batch_size                         = var.consumer_batch_size
  parallelization_factor             = var.consumer_parallelization
  maximum_batching_window_in_seconds = var.max_batching_window_seconds

  bisect_batch_on_function_error = true
  maximum_retry_attempts = 3
  maximum_record_age_in_seconds = 3600
}
