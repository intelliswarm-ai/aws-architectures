# =============================================================================
# CloudTrail Module - Audit Logging
# =============================================================================

locals {
  prefix      = "${var.project_name}-${var.environment}"
  bucket_name = var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.prefix}-cloudtrail-logs"

  common_tags = merge(var.tags, {
    Module      = "cloudtrail"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# S3 Bucket for CloudTrail Logs
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "cloudtrail" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket        = local.bucket_name
  force_destroy = var.environment != "prod"

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "cloudtrail" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cloudtrail" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != null ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn
    }
    bucket_key_enabled = var.kms_key_arn != null
  }
}

resource "aws_s3_bucket_public_access_block" "cloudtrail" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "cloudtrail" {
  count = var.s3_bucket_name == "" && var.log_retention_days > 0 ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    expiration {
      days = var.log_retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}

# S3 Bucket Policy for CloudTrail
resource "aws_s3_bucket_policy" "cloudtrail" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket = aws_s3_bucket.cloudtrail[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSCloudTrailAclCheck"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.cloudtrail[0].arn
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = "arn:aws:cloudtrail:${var.aws_region}:${var.aws_account_id}:trail/${local.prefix}-trail"
          }
        }
      },
      {
        Sid    = "AWSCloudTrailWrite"
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.cloudtrail[0].arn}/${var.s3_key_prefix}/AWSLogs/${var.aws_account_id}/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl"  = "bucket-owner-full-control"
            "AWS:SourceArn" = "arn:aws:cloudtrail:${var.aws_region}:${var.aws_account_id}:trail/${local.prefix}-trail"
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# CloudWatch Log Group for CloudTrail
# -----------------------------------------------------------------------------
resource "aws_cloudwatch_log_group" "cloudtrail" {
  count = var.enable_cloudwatch_logs ? 1 : 0

  name              = "/aws/cloudtrail/${local.prefix}"
  retention_in_days = var.cloudwatch_log_retention_days
  kms_key_id        = var.kms_key_arn

  tags = local.common_tags
}

# IAM Role for CloudWatch Logs
resource "aws_iam_role" "cloudtrail_cloudwatch" {
  count = var.enable_cloudwatch_logs ? 1 : 0

  name = "${local.prefix}-cloudtrail-cloudwatch"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "cloudtrail.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "cloudtrail_cloudwatch" {
  count = var.enable_cloudwatch_logs ? 1 : 0

  name = "${local.prefix}-cloudtrail-cloudwatch"
  role = aws_iam_role.cloudtrail_cloudwatch[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "CloudWatchLogsWrite"
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.cloudtrail[0].arn}:*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# CloudTrail
# -----------------------------------------------------------------------------
resource "aws_cloudtrail" "this" {
  name                          = "${local.prefix}-trail"
  s3_bucket_name                = var.s3_bucket_name != "" ? var.s3_bucket_name : aws_s3_bucket.cloudtrail[0].id
  s3_key_prefix                 = var.s3_key_prefix
  include_global_service_events = var.include_global_service_events
  is_multi_region_trail         = var.is_multi_region
  enable_log_file_validation    = var.enable_log_file_validation
  kms_key_id                    = var.kms_key_arn

  cloud_watch_logs_group_arn = var.enable_cloudwatch_logs ? "${aws_cloudwatch_log_group.cloudtrail[0].arn}:*" : null
  cloud_watch_logs_role_arn  = var.enable_cloudwatch_logs ? aws_iam_role.cloudtrail_cloudwatch[0].arn : null

  # Management Events
  dynamic "event_selector" {
    for_each = var.enable_management_events ? [1] : []
    content {
      read_write_type           = var.management_event_read_write
      include_management_events = true

      # S3 Data Events
      dynamic "data_resource" {
        for_each = var.enable_data_events && length(var.data_event_s3_buckets) > 0 ? [1] : (var.enable_data_events ? [1] : [])
        content {
          type   = "AWS::S3::Object"
          values = length(var.data_event_s3_buckets) > 0 ? var.data_event_s3_buckets : ["arn:aws:s3"]
        }
      }

      # Lambda Data Events
      dynamic "data_resource" {
        for_each = var.enable_data_events && length(var.data_event_lambda_functions) > 0 ? [1] : []
        content {
          type   = "AWS::Lambda::Function"
          values = var.data_event_lambda_functions
        }
      }
    }
  }

  # DynamoDB Data Events (separate selector)
  dynamic "event_selector" {
    for_each = var.enable_data_events && length(var.data_event_dynamodb_tables) > 0 ? [1] : []
    content {
      read_write_type           = "All"
      include_management_events = false

      data_resource {
        type   = "AWS::DynamoDB::Table"
        values = var.data_event_dynamodb_tables
      }
    }
  }

  # Insights (if enabled)
  dynamic "insight_selector" {
    for_each = var.enable_insights ? [1] : []
    content {
      insight_type = "ApiCallRateInsight"
    }
  }

  dynamic "insight_selector" {
    for_each = var.enable_insights ? [1] : []
    content {
      insight_type = "ApiErrorRateInsight"
    }
  }

  tags = local.common_tags

  depends_on = [aws_s3_bucket_policy.cloudtrail]
}
