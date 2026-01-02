################################################################################
# IAM Roles and Policies Module
################################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Lambda execution assume role policy
data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

################################################################################
# GPS Producer Role
################################################################################

resource "aws_iam_role" "producer" {
  name               = "${var.project_name}-producer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = var.tags
}

data "aws_iam_policy_document" "producer" {
  # CloudWatch Logs
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"]
  }

  # Kinesis write access
  statement {
    sid = "KinesisWrite"
    actions = [
      "kinesis:PutRecord",
      "kinesis:PutRecords",
      "kinesis:DescribeStream",
    ]
    resources = [var.kinesis_stream_arn]
  }

  # X-Ray tracing
  statement {
    sid = "XRayTracing"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "producer" {
  name   = "${var.project_name}-producer-policy"
  role   = aws_iam_role.producer.id
  policy = data.aws_iam_policy_document.producer.json
}

################################################################################
# Dashboard Consumer Role
################################################################################

resource "aws_iam_role" "dashboard_consumer" {
  name               = "${var.project_name}-dashboard-consumer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = var.tags
}

data "aws_iam_policy_document" "dashboard_consumer" {
  # CloudWatch Logs
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"]
  }

  # Kinesis read access
  statement {
    sid = "KinesisRead"
    actions = [
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:DescribeStream",
      "kinesis:DescribeStreamSummary",
      "kinesis:ListShards",
      "kinesis:ListStreams",
    ]
    resources = [var.kinesis_stream_arn]
  }

  # DynamoDB write access
  statement {
    sid = "DynamoDBWrite"
    actions = [
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:GetItem",
    ]
    resources = var.dynamodb_table_arns
  }

  # X-Ray tracing
  statement {
    sid = "XRayTracing"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "dashboard_consumer" {
  name   = "${var.project_name}-dashboard-consumer-policy"
  role   = aws_iam_role.dashboard_consumer.id
  policy = data.aws_iam_policy_document.dashboard_consumer.json
}

################################################################################
# Geofence Consumer Role
################################################################################

resource "aws_iam_role" "geofence_consumer" {
  name               = "${var.project_name}-geofence-consumer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = var.tags
}

data "aws_iam_policy_document" "geofence_consumer" {
  # CloudWatch Logs
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"]
  }

  # Kinesis read access
  statement {
    sid = "KinesisRead"
    actions = [
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:DescribeStream",
      "kinesis:DescribeStreamSummary",
      "kinesis:ListShards",
      "kinesis:ListStreams",
    ]
    resources = [var.kinesis_stream_arn]
  }

  # DynamoDB read access (for geofence definitions)
  statement {
    sid = "DynamoDBRead"
    actions = [
      "dynamodb:Scan",
      "dynamodb:Query",
      "dynamodb:GetItem",
    ]
    resources = var.dynamodb_table_arns
  }

  # SNS publish access
  statement {
    sid = "SNSPublish"
    actions = [
      "sns:Publish",
    ]
    resources = [var.sns_topic_arn]
  }

  # X-Ray tracing
  statement {
    sid = "XRayTracing"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "geofence_consumer" {
  name   = "${var.project_name}-geofence-consumer-policy"
  role   = aws_iam_role.geofence_consumer.id
  policy = data.aws_iam_policy_document.geofence_consumer.json
}

################################################################################
# Archive Consumer Role
################################################################################

resource "aws_iam_role" "archive_consumer" {
  name               = "${var.project_name}-archive-consumer-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = var.tags
}

data "aws_iam_policy_document" "archive_consumer" {
  # CloudWatch Logs
  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"]
  }

  # Kinesis read access
  statement {
    sid = "KinesisRead"
    actions = [
      "kinesis:GetRecords",
      "kinesis:GetShardIterator",
      "kinesis:DescribeStream",
      "kinesis:DescribeStreamSummary",
      "kinesis:ListShards",
      "kinesis:ListStreams",
    ]
    resources = [var.kinesis_stream_arn]
  }

  # S3 write access
  statement {
    sid = "S3Write"
    actions = [
      "s3:PutObject",
      "s3:PutObjectAcl",
      "s3:GetObject",
      "s3:ListBucket",
    ]
    resources = [
      var.s3_bucket_arn,
      "${var.s3_bucket_arn}/*",
    ]
  }

  # X-Ray tracing
  statement {
    sid = "XRayTracing"
    actions = [
      "xray:PutTraceSegments",
      "xray:PutTelemetryRecords",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "archive_consumer" {
  name   = "${var.project_name}-archive-consumer-policy"
  role   = aws_iam_role.archive_consumer.id
  policy = data.aws_iam_policy_document.archive_consumer.json
}
