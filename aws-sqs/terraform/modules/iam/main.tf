################################################################################
# IAM Module - Roles and Policies for Banking Platform
################################################################################

# EC2 Instance Role
resource "aws_iam_role" "ec2_processor" {
  name = "${var.project_name}-ec2-processor-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# EC2 Instance Profile
resource "aws_iam_instance_profile" "ec2_processor" {
  name = "${var.project_name}-ec2-processor-profile"
  role = aws_iam_role.ec2_processor.name
}

# SQS Policy for EC2
resource "aws_iam_role_policy" "ec2_sqs" {
  name = "${var.project_name}-ec2-sqs-policy"
  role = aws_iam_role.ec2_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = var.sqs_queue_arn
      }
    ]
  })
}

# DynamoDB Policy for EC2
resource "aws_iam_role_policy" "ec2_dynamodb" {
  name = "${var.project_name}-ec2-dynamodb-policy"
  role = aws_iam_role.ec2_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = var.dynamodb_table_arns
      }
    ]
  })
}

# S3 Policy for EC2 (for application deployment)
resource "aws_iam_role_policy" "ec2_s3" {
  name = "${var.project_name}-ec2-s3-policy"
  role = aws_iam_role.ec2_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.s3_bucket_arn,
          "${var.s3_bucket_arn}/*"
        ]
      }
    ]
  })
}

# CloudWatch Policy for EC2
resource "aws_iam_role_policy" "ec2_cloudwatch" {
  name = "${var.project_name}-ec2-cloudwatch-policy"
  role = aws_iam_role.ec2_processor.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData",
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogStreams"
        ]
        Resource = "*"
      }
    ]
  })
}

# SSM Policy for EC2 (for Session Manager access)
resource "aws_iam_role_policy_attachment" "ec2_ssm" {
  role       = aws_iam_role.ec2_processor.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Lambda Execution Role
resource "aws_iam_role" "lambda" {
  name = "${var.project_name}-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Lambda Basic Execution
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Lambda SQS Policy
resource "aws_iam_role_policy" "lambda_sqs" {
  name = "${var.project_name}-lambda-sqs-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sqs:SendMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl"
        ]
        Resource = var.sqs_queue_arn
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes"
        ]
        Resource = var.sqs_dlq_arn
      }
    ]
  })
}

# Lambda DynamoDB Policy
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "${var.project_name}-lambda-dynamodb-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = var.dynamodb_table_arns
      }
    ]
  })
}

# Lambda CloudWatch Policy
resource "aws_iam_role_policy" "lambda_cloudwatch" {
  name = "${var.project_name}-lambda-cloudwatch-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cloudwatch:PutMetricData"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda Auto Scaling Policy (for metrics handler)
resource "aws_iam_role_policy" "lambda_autoscaling" {
  name = "${var.project_name}-lambda-autoscaling-policy"
  role = aws_iam_role.lambda.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "autoscaling:DescribeAutoScalingGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Lambda X-Ray Tracing
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}
