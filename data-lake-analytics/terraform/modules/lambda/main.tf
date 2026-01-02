# ---------------------------------------------------------------------------------------------------------------------
# LAMBDA FUNCTIONS FOR DATA LAKE OPERATIONS
# ---------------------------------------------------------------------------------------------------------------------

locals {
  lambda_env_vars = {
    AWS_REGION           = data.aws_region.current.name
    RAW_BUCKET           = var.raw_bucket_name
    PROCESSED_BUCKET     = var.processed_bucket_name
    RESULTS_BUCKET       = var.results_bucket_name
    GLUE_DATABASE        = var.glue_database
    ATHENA_WORKGROUP     = var.athena_workgroup
    GLUE_ETL_JOB_NAME    = var.glue_etl_job_name
    GLUE_CRAWLER_NAME    = var.glue_crawler_name
    ATHENA_QUERY_TIMEOUT = tostring(var.athena_query_timeout)
    LOG_LEVEL            = var.log_level
  }
}

data "aws_region" "current" {}

# Lambda Layer for shared dependencies
resource "aws_lambda_layer_version" "dependencies" {
  filename            = "${path.module}/../../../dist/layer.zip"
  layer_name          = "${var.project_name}-${var.environment}-dependencies"
  compatible_runtimes = [var.runtime]
  description         = "Shared dependencies for data lake functions"

  lifecycle {
    create_before_destroy = true
  }
}

# Ingest Lambda Function
resource "aws_lambda_function" "ingest" {
  filename         = "${path.module}/../../../dist/ingest.zip"
  function_name    = "${var.project_name}-${var.environment}-ingest"
  role             = var.lambda_role_arn
  handler          = "src.handlers.ingest_handler.handler"
  runtime          = var.runtime
  memory_size      = var.memory_size
  timeout          = var.timeout
  source_code_hash = filebase64sha256("${path.module}/../../../dist/ingest.zip")

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = local.lambda_env_vars
  }
}

resource "aws_lambda_function_url" "ingest" {
  function_name      = aws_lambda_function.ingest.function_name
  authorization_type = var.environment == "prod" ? "AWS_IAM" : "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["content-type", "x-amz-date", "authorization"]
    expose_headers    = ["x-amz-request-id"]
    max_age           = 86400
  }
}

# ETL Lambda Function
resource "aws_lambda_function" "etl" {
  filename         = "${path.module}/../../../dist/etl.zip"
  function_name    = "${var.project_name}-${var.environment}-etl"
  role             = var.lambda_role_arn
  handler          = "src.handlers.etl_handler.handler"
  runtime          = var.runtime
  memory_size      = var.memory_size
  timeout          = 300 # ETL operations may take longer
  source_code_hash = filebase64sha256("${path.module}/../../../dist/etl.zip")

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = local.lambda_env_vars
  }
}

resource "aws_lambda_function_url" "etl" {
  function_name      = aws_lambda_function.etl.function_name
  authorization_type = "AWS_IAM"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["POST"]
    allow_headers     = ["content-type", "x-amz-date", "authorization"]
    max_age           = 86400
  }
}

# Query Lambda Function
resource "aws_lambda_function" "query" {
  filename         = "${path.module}/../../../dist/query.zip"
  function_name    = "${var.project_name}-${var.environment}-query"
  role             = var.lambda_role_arn
  handler          = "src.handlers.query_handler.handler"
  runtime          = var.runtime
  memory_size      = var.memory_size
  timeout          = var.timeout
  source_code_hash = filebase64sha256("${path.module}/../../../dist/query.zip")

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = local.lambda_env_vars
  }
}

resource "aws_lambda_function_url" "query" {
  function_name      = aws_lambda_function.query.function_name
  authorization_type = var.environment == "prod" ? "AWS_IAM" : "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST"]
    allow_headers     = ["content-type", "x-amz-date", "authorization"]
    expose_headers    = ["x-amz-request-id"]
    max_age           = 86400
  }
}

# API Lambda Function (combined API Gateway handler)
resource "aws_lambda_function" "api" {
  filename         = "${path.module}/../../../dist/api.zip"
  function_name    = "${var.project_name}-${var.environment}-api"
  role             = var.lambda_role_arn
  handler          = "src.handlers.api_handler.handler"
  runtime          = var.runtime
  memory_size      = var.memory_size
  timeout          = var.timeout
  source_code_hash = filebase64sha256("${path.module}/../../../dist/api.zip")

  layers = [aws_lambda_layer_version.dependencies.arn]

  environment {
    variables = local.lambda_env_vars
  }
}

resource "aws_lambda_function_url" "api" {
  function_name      = aws_lambda_function.api.function_name
  authorization_type = var.environment == "prod" ? "AWS_IAM" : "NONE"

  cors {
    allow_credentials = true
    allow_origins     = ["*"]
    allow_methods     = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allow_headers     = ["content-type", "x-amz-date", "authorization", "x-api-key"]
    expose_headers    = ["x-amz-request-id"]
    max_age           = 86400
  }
}

# S3 trigger for ingest function (optional - for direct S3 uploads)
resource "aws_lambda_permission" "s3_ingest" {
  statement_id  = "AllowS3Invoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingest.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = "arn:aws:s3:::${var.raw_bucket_name}"
}
