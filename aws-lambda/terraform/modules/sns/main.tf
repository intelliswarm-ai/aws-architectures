# Success notification topic
resource "aws_sns_topic" "success" {
  name = "${var.topic_prefix}-success"

  # Enable server-side encryption
  kms_master_key_id = var.kms_key_id

  tags = var.tags
}

# Failure notification topic
resource "aws_sns_topic" "failure" {
  name = "${var.topic_prefix}-failure"

  # Enable server-side encryption
  kms_master_key_id = var.kms_key_id

  tags = var.tags
}

# Email subscription for success topic
resource "aws_sns_topic_subscription" "success_email" {
  count     = var.email_endpoint != "" ? 1 : 0
  topic_arn = aws_sns_topic.success.arn
  protocol  = "email"
  endpoint  = var.email_endpoint
}

# Email subscription for failure topic
resource "aws_sns_topic_subscription" "failure_email" {
  count     = var.email_endpoint != "" ? 1 : 0
  topic_arn = aws_sns_topic.failure.arn
  protocol  = "email"
  endpoint  = var.email_endpoint
}

# Lambda subscription for notification handler
resource "aws_sns_topic_subscription" "success_lambda" {
  count     = var.lambda_endpoint_arn != "" ? 1 : 0
  topic_arn = aws_sns_topic.success.arn
  protocol  = "lambda"
  endpoint  = var.lambda_endpoint_arn
}

resource "aws_sns_topic_subscription" "failure_lambda" {
  count     = var.lambda_endpoint_arn != "" ? 1 : 0
  topic_arn = aws_sns_topic.failure.arn
  protocol  = "lambda"
  endpoint  = var.lambda_endpoint_arn
}

# Topic policy
resource "aws_sns_topic_policy" "success" {
  arn = aws_sns_topic.success.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowStepFunctionsPublish"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.success.arn
      },
      {
        Sid    = "AllowLambdaPublish"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.success.arn
      }
    ]
  })
}

resource "aws_sns_topic_policy" "failure" {
  arn = aws_sns_topic.failure.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowStepFunctionsPublish"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.failure.arn
      },
      {
        Sid    = "AllowLambdaPublish"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.failure.arn
      }
    ]
  })
}
