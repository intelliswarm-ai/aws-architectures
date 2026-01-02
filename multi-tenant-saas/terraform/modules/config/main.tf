# =============================================================================
# AWS Config Module - Compliance Monitoring
# =============================================================================

locals {
  prefix      = "${var.project_name}-${var.environment}"
  bucket_name = var.s3_bucket_name != "" ? var.s3_bucket_name : "${local.prefix}-config-logs"

  common_tags = merge(var.tags, {
    Module      = "config"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# S3 Bucket for Config Logs
# -----------------------------------------------------------------------------
resource "aws_s3_bucket" "config" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket        = local.bucket_name
  force_destroy = var.environment != "prod"

  tags = local.common_tags
}

resource "aws_s3_bucket_versioning" "config" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket = aws_s3_bucket.config[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "config" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket = aws_s3_bucket.config[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "config" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket = aws_s3_bucket.config[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "config" {
  count = var.s3_bucket_name == "" && var.log_retention_days > 0 ? 1 : 0

  bucket = aws_s3_bucket.config[0].id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    expiration {
      days = var.log_retention_days
    }
  }
}

# S3 Bucket Policy for Config
resource "aws_s3_bucket_policy" "config" {
  count = var.s3_bucket_name == "" ? 1 : 0

  bucket = aws_s3_bucket.config[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AWSConfigBucketPermissionsCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:GetBucketAcl"
        Resource = aws_s3_bucket.config[0].arn
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = var.aws_account_id
          }
        }
      },
      {
        Sid    = "AWSConfigBucketExistenceCheck"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:ListBucket"
        Resource = aws_s3_bucket.config[0].arn
        Condition = {
          StringEquals = {
            "AWS:SourceAccount" = var.aws_account_id
          }
        }
      },
      {
        Sid    = "AWSConfigBucketDelivery"
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action   = "s3:PutObject"
        Resource = "${aws_s3_bucket.config[0].arn}/${var.s3_key_prefix}/AWSLogs/${var.aws_account_id}/Config/*"
        Condition = {
          StringEquals = {
            "s3:x-amz-acl"      = "bucket-owner-full-control"
            "AWS:SourceAccount" = var.aws_account_id
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# IAM Role for Config
# -----------------------------------------------------------------------------
resource "aws_iam_role" "config" {
  name = "${local.prefix}-config-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "config.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "config" {
  role       = aws_iam_role.config.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
}

resource "aws_iam_role_policy" "config_s3" {
  name = "${local.prefix}-config-s3"
  role = aws_iam_role.config.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl"
        ]
        Resource = "${var.s3_bucket_name != "" ? "arn:aws:s3:::${var.s3_bucket_name}" : aws_s3_bucket.config[0].arn}/${var.s3_key_prefix}/AWSLogs/${var.aws_account_id}/Config/*"
        Condition = {
          StringLike = {
            "s3:x-amz-acl" = "bucket-owner-full-control"
          }
        }
      },
      {
        Effect   = "Allow"
        Action   = "s3:GetBucketAcl"
        Resource = var.s3_bucket_name != "" ? "arn:aws:s3:::${var.s3_bucket_name}" : aws_s3_bucket.config[0].arn
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Config Recorder
# -----------------------------------------------------------------------------
resource "aws_config_configuration_recorder" "this" {
  name     = "${local.prefix}-recorder"
  role_arn = aws_iam_role.config.arn

  recording_group {
    all_supported                 = var.all_supported
    include_global_resource_types = var.include_global_resources
    resource_types                = var.all_supported ? null : var.resource_types
  }
}

resource "aws_config_delivery_channel" "this" {
  name           = "${local.prefix}-delivery"
  s3_bucket_name = var.s3_bucket_name != "" ? var.s3_bucket_name : aws_s3_bucket.config[0].id
  s3_key_prefix  = var.s3_key_prefix

  snapshot_delivery_properties {
    delivery_frequency = "TwentyFour_Hours"
  }

  depends_on = [aws_config_configuration_recorder.this]
}

resource "aws_config_configuration_recorder_status" "this" {
  name       = aws_config_configuration_recorder.this.name
  is_enabled = var.recording_enabled

  depends_on = [aws_config_delivery_channel.this]
}

# -----------------------------------------------------------------------------
# AWS Config Managed Rules
# -----------------------------------------------------------------------------
# Encrypted Volumes
resource "aws_config_config_rule" "encrypted_volumes" {
  count = var.enable_encrypted_volumes ? 1 : 0

  name = "${local.prefix}-encrypted-volumes"

  source {
    owner             = "AWS"
    source_identifier = "ENCRYPTED_VOLUMES"
  }

  depends_on = [aws_config_configuration_recorder.this]

  tags = local.common_tags
}

# S3 Bucket Encryption
resource "aws_config_config_rule" "s3_encryption" {
  count = var.enable_s3_bucket_encryption ? 1 : 0

  name = "${local.prefix}-s3-bucket-encryption"

  source {
    owner             = "AWS"
    source_identifier = "S3_BUCKET_SERVER_SIDE_ENCRYPTION_ENABLED"
  }

  depends_on = [aws_config_configuration_recorder.this]

  tags = local.common_tags
}

# Root Account MFA
resource "aws_config_config_rule" "root_mfa" {
  count = var.enable_root_mfa ? 1 : 0

  name = "${local.prefix}-root-account-mfa"

  source {
    owner             = "AWS"
    source_identifier = "ROOT_ACCOUNT_MFA_ENABLED"
  }

  depends_on = [aws_config_configuration_recorder.this]

  tags = local.common_tags
}

# IAM Password Policy
resource "aws_config_config_rule" "iam_password_policy" {
  count = var.enable_iam_password_policy ? 1 : 0

  name = "${local.prefix}-iam-password-policy"

  source {
    owner             = "AWS"
    source_identifier = "IAM_PASSWORD_POLICY"
  }

  input_parameters = jsonencode({
    RequireUppercaseCharacters = "true"
    RequireLowercaseCharacters = "true"
    RequireSymbols             = "true"
    RequireNumbers             = "true"
    MinimumPasswordLength      = "14"
  })

  depends_on = [aws_config_configuration_recorder.this]

  tags = local.common_tags
}

# RDS Encryption
resource "aws_config_config_rule" "rds_encryption" {
  count = var.enable_rds_encryption ? 1 : 0

  name = "${local.prefix}-rds-storage-encrypted"

  source {
    owner             = "AWS"
    source_identifier = "RDS_STORAGE_ENCRYPTED"
  }

  depends_on = [aws_config_configuration_recorder.this]

  tags = local.common_tags
}

# CloudTrail Enabled
resource "aws_config_config_rule" "cloudtrail_enabled" {
  count = var.enable_cloudtrail_enabled ? 1 : 0

  name = "${local.prefix}-cloudtrail-enabled"

  source {
    owner             = "AWS"
    source_identifier = "CLOUD_TRAIL_ENABLED"
  }

  depends_on = [aws_config_configuration_recorder.this]

  tags = local.common_tags
}

# Lambda Concurrency Check
resource "aws_config_config_rule" "lambda_concurrency" {
  count = var.enable_lambda_concurrency ? 1 : 0

  name = "${local.prefix}-lambda-concurrency"

  source {
    owner             = "AWS"
    source_identifier = "LAMBDA_CONCURRENCY_CHECK"
  }

  depends_on = [aws_config_configuration_recorder.this]

  tags = local.common_tags
}

# DynamoDB Autoscaling
resource "aws_config_config_rule" "dynamodb_autoscaling" {
  count = var.enable_dynamodb_autoscaling ? 1 : 0

  name = "${local.prefix}-dynamodb-autoscaling"

  source {
    owner             = "AWS"
    source_identifier = "DYNAMODB_AUTOSCALING_ENABLED"
  }

  depends_on = [aws_config_configuration_recorder.this]

  tags = local.common_tags
}
