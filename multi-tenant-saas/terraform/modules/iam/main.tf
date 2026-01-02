# =============================================================================
# IAM Module - Multi-Tenant Enterprise IAM Patterns
# =============================================================================

locals {
  prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Module      = "iam"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# Permission Boundary - Prevents privilege escalation
# -----------------------------------------------------------------------------
resource "aws_iam_policy" "permission_boundary" {
  count = var.enable_permission_boundary ? 1 : 0

  name        = "${local.prefix}-permission-boundary"
  description = "Permission boundary for all roles in ${var.project_name}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Allow most actions within allowed regions
      {
        Sid    = "AllowRegionalActions"
        Effect = "Allow"
        Action = "*"
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:RequestedRegion" = var.allowed_regions
          }
        }
      },
      # Allow global services (IAM read, STS, etc.)
      {
        Sid    = "AllowGlobalServices"
        Effect = "Allow"
        Action = [
          "iam:Get*",
          "iam:List*",
          "sts:*",
          "cloudfront:*",
          "route53:*",
          "waf:*",
          "wafv2:*",
          "waf-regional:*"
        ]
        Resource = "*"
      },
      # Deny dangerous IAM actions
      {
        Sid    = "DenyDangerousIAMActions"
        Effect = "Deny"
        Action = [
          "iam:CreateUser",
          "iam:CreateAccessKey",
          "iam:DeleteAccountPasswordPolicy",
          "iam:UpdateAccountPasswordPolicy",
          "iam:CreateSAMLProvider",
          "iam:DeleteSAMLProvider",
          "iam:UpdateSAMLProvider"
        ]
        Resource = "*"
      },
      # Deny creating roles without permission boundary
      {
        Sid    = "DenyRolesWithoutBoundary"
        Effect = "Deny"
        Action = [
          "iam:CreateRole",
          "iam:PutRolePermissionsBoundary"
        ]
        Resource = "*"
        Condition = {
          StringNotEquals = {
            "iam:PermissionsBoundary" = "arn:aws:iam::${var.aws_account_id}:policy/${local.prefix}-permission-boundary"
          }
        }
      },
      # Deny access to denied services
      {
        Sid      = "DenyBlockedServices"
        Effect   = "Deny"
        Action   = [for svc in var.denied_services : "${svc}:*"]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Lambda Execution Role (with multi-tenant context)
# -----------------------------------------------------------------------------
resource "aws_iam_role" "lambda_execution" {
  name = "${local.prefix}-lambda-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  permissions_boundary = var.enable_permission_boundary ? aws_iam_policy.permission_boundary[0].arn : null

  tags = local.common_tags
}

# Basic Lambda execution (logs)
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# VPC access for Lambda
resource "aws_iam_role_policy_attachment" "lambda_vpc" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaVPCAccessExecutionRole"
}

# X-Ray tracing
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# -----------------------------------------------------------------------------
# Multi-Tenant Data Access Policy
# -----------------------------------------------------------------------------
resource "aws_iam_policy" "multi_tenant_data_access" {
  name        = "${local.prefix}-multi-tenant-data-access"
  description = "Policy for accessing tenant-scoped data"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # DynamoDB access with tenant isolation
      {
        Sid    = "DynamoDBTenantAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem",
          "dynamodb:BatchWriteItem"
        ]
        Resource = length(var.dynamodb_table_arns) > 0 ? var.dynamodb_table_arns : ["arn:aws:dynamodb:${var.aws_region}:${var.aws_account_id}:table/${local.prefix}-*"]
      },
      # DynamoDB indexes
      {
        Sid    = "DynamoDBIndexAccess"
        Effect = "Allow"
        Action = [
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = length(var.dynamodb_table_arns) > 0 ? [for arn in var.dynamodb_table_arns : "${arn}/index/*"] : ["arn:aws:dynamodb:${var.aws_region}:${var.aws_account_id}:table/${local.prefix}-*/index/*"]
      },
      # SQS access
      {
        Sid    = "SQSAccess"
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = length(var.sqs_queue_arns) > 0 ? var.sqs_queue_arns : ["arn:aws:sqs:${var.aws_region}:${var.aws_account_id}:${local.prefix}-*"]
      },
      # SNS access
      {
        Sid    = "SNSAccess"
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = length(var.sns_topic_arns) > 0 ? var.sns_topic_arns : ["arn:aws:sns:${var.aws_region}:${var.aws_account_id}:${local.prefix}-*"]
      },
      # S3 access (tenant-prefixed objects)
      {
        Sid    = "S3Access"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = length(var.s3_bucket_arns) > 0 ? concat(var.s3_bucket_arns, [for arn in var.s3_bucket_arns : "${arn}/*"]) : [
          "arn:aws:s3:::${local.prefix}-*",
          "arn:aws:s3:::${local.prefix}-*/*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_data_access" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.multi_tenant_data_access.arn
}

# -----------------------------------------------------------------------------
# Secrets and Parameters Access Policy
# -----------------------------------------------------------------------------
resource "aws_iam_policy" "secrets_access" {
  name        = "${local.prefix}-secrets-access"
  description = "Policy for accessing secrets and parameters"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      # Secrets Manager
      {
        Sid    = "SecretsManagerAccess"
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = length(var.secrets_arns) > 0 ? var.secrets_arns : ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${local.prefix}/*"]
      },
      # SSM Parameter Store
      {
        Sid    = "SSMParameterAccess"
        Effect = "Allow"
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters",
          "ssm:GetParametersByPath"
        ]
        Resource = length(var.ssm_parameter_arns) > 0 ? var.ssm_parameter_arns : ["arn:aws:ssm:${var.aws_region}:${var.aws_account_id}:parameter/${local.prefix}/*"]
      },
      # KMS for decryption
      {
        Sid    = "KMSDecrypt"
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey*"
        ]
        Resource = var.kms_key_arn != null ? [var.kms_key_arn] : ["arn:aws:kms:${var.aws_region}:${var.aws_account_id}:key/*"]
        Condition = {
          StringEquals = {
            "kms:ViaService" = [
              "secretsmanager.${var.aws_region}.amazonaws.com",
              "ssm.${var.aws_region}.amazonaws.com"
            ]
          }
        }
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_secrets" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.secrets_access.arn
}

# -----------------------------------------------------------------------------
# GenAI/Bedrock Access Policy
# -----------------------------------------------------------------------------
resource "aws_iam_policy" "bedrock_access" {
  name        = "${local.prefix}-bedrock-access"
  description = "Policy for accessing Amazon Bedrock for GenAI"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvoke"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = [
          "arn:aws:bedrock:${var.aws_region}::foundation-model/*",
          "arn:aws:bedrock:${var.aws_region}:${var.aws_account_id}:provisioned-model/*"
        ]
      },
      {
        Sid    = "BedrockModelAccess"
        Effect = "Allow"
        Action = [
          "bedrock:GetFoundationModel",
          "bedrock:ListFoundationModels"
        ]
        Resource = "*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_bedrock" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.bedrock_access.arn
}

# -----------------------------------------------------------------------------
# EventBridge Access Policy
# -----------------------------------------------------------------------------
resource "aws_iam_policy" "eventbridge_access" {
  name        = "${local.prefix}-eventbridge-access"
  description = "Policy for EventBridge access"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "EventBridgePutEvents"
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = [
          "arn:aws:events:${var.aws_region}:${var.aws_account_id}:event-bus/${local.prefix}-*"
        ]
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "lambda_eventbridge" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = aws_iam_policy.eventbridge_access.arn
}

# -----------------------------------------------------------------------------
# Cross-Account Access Role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "cross_account" {
  count = var.enable_cross_account && length(var.trusted_account_ids) > 0 ? 1 : 0

  name = "${local.prefix}-cross-account"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          AWS = [for id in var.trusted_account_ids : "arn:aws:iam::${id}:root"]
        }
        Action = "sts:AssumeRole"
        Condition = var.external_id != "" ? {
          StringEquals = {
            "sts:ExternalId" = var.external_id
          }
        } : null
      }
    ]
  })

  permissions_boundary = var.enable_permission_boundary ? aws_iam_policy.permission_boundary[0].arn : null

  tags = local.common_tags
}

# Cross-account read-only access
resource "aws_iam_role_policy" "cross_account_readonly" {
  count = var.enable_cross_account && length(var.trusted_account_ids) > 0 ? 1 : 0

  name = "${local.prefix}-cross-account-readonly"
  role = aws_iam_role.cross_account[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ReadOnlyDynamoDB"
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:Scan",
          "dynamodb:BatchGetItem"
        ]
        Resource = length(var.dynamodb_table_arns) > 0 ? var.dynamodb_table_arns : ["arn:aws:dynamodb:${var.aws_region}:${var.aws_account_id}:table/${local.prefix}-*"]
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Secrets Manager Rotation Role
# -----------------------------------------------------------------------------
resource "aws_iam_role" "secrets_rotation" {
  name = "${local.prefix}-secrets-rotation"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  permissions_boundary = var.enable_permission_boundary ? aws_iam_policy.permission_boundary[0].arn : null

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "secrets_rotation_basic" {
  role       = aws_iam_role.secrets_rotation.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "secrets_rotation" {
  name = "${local.prefix}-secrets-rotation-policy"
  role = aws_iam_role.secrets_rotation.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:PutSecretValue",
          "secretsmanager:UpdateSecretVersionStage",
          "secretsmanager:DescribeSecret"
        ]
        Resource = length(var.secrets_arns) > 0 ? var.secrets_arns : ["arn:aws:secretsmanager:${var.aws_region}:${var.aws_account_id}:secret:${local.prefix}/*"]
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:GenerateDataKey"
        ]
        Resource = var.kms_key_arn != null ? [var.kms_key_arn] : ["arn:aws:kms:${var.aws_region}:${var.aws_account_id}:key/*"]
      }
    ]
  })
}
