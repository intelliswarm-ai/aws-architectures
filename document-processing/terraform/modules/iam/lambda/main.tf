# IAM Role for Lambda Functions

resource "aws_iam_role" "lambda_exec" {
  name = "${var.project_prefix}-lambda-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

# Basic Lambda execution
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# X-Ray tracing
resource "aws_iam_role_policy_attachment" "lambda_xray" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AWSXRayDaemonWriteAccess"
}

# S3 access
resource "aws_iam_role_policy" "s3_access" {
  name = "${var.project_prefix}-lambda-s3-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket",
          "s3:HeadObject"
        ]
        Resource = [
          var.raw_bucket_arn,
          "${var.raw_bucket_arn}/*",
          var.processed_bucket_arn,
          "${var.processed_bucket_arn}/*",
          var.model_bucket_arn,
          "${var.model_bucket_arn}/*"
        ]
      }
    ]
  })
}

# DynamoDB access
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "${var.project_prefix}-lambda-dynamodb-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = [
        var.documents_table_arn,
        "${var.documents_table_arn}/index/*"
      ]
    }]
  })
}

# SQS access
resource "aws_iam_role_policy" "sqs_access" {
  name = "${var.project_prefix}-lambda-sqs-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "sqs:SendMessage",
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ]
      Resource = [var.processing_queue_arn, var.dlq_arn]
    }]
  })
}

# SNS access
resource "aws_iam_role_policy" "sns_access" {
  name = "${var.project_prefix}-lambda-sns-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sns:Publish"]
      Resource = [var.success_topic_arn, var.failure_topic_arn, var.alert_topic_arn]
    }]
  })
}

# Step Functions access
resource "aws_iam_role_policy" "sfn_access" {
  name = "${var.project_prefix}-lambda-sfn-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "states:StartExecution",
        "states:DescribeExecution"
      ]
      Resource = [var.workflow_arn]
    }]
  })
}

# AI Services access (Textract, Comprehend, Rekognition, Transcribe)
resource "aws_iam_role_policy" "ai_services" {
  name = "${var.project_prefix}-lambda-ai-services-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "textract:DetectDocumentText",
          "textract:AnalyzeDocument",
          "textract:StartDocumentTextDetection",
          "textract:StartDocumentAnalysis",
          "textract:GetDocumentTextDetection",
          "textract:GetDocumentAnalysis"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "comprehend:DetectDominantLanguage",
          "comprehend:DetectEntities",
          "comprehend:DetectKeyPhrases",
          "comprehend:DetectSentiment",
          "comprehend:DetectPiiEntities",
          "comprehend:BatchDetectEntities",
          "comprehend:ClassifyDocument"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "rekognition:DetectLabels",
          "rekognition:DetectText",
          "rekognition:DetectModerationLabels",
          "rekognition:DetectFaces",
          "rekognition:CompareFaces",
          "rekognition:RecognizeCelebrities"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "transcribe:StartTranscriptionJob",
          "transcribe:GetTranscriptionJob",
          "transcribe:DeleteTranscriptionJob"
        ]
        Resource = "*"
      }
    ]
  })
}

# Bedrock access
resource "aws_iam_role_policy" "bedrock_access" {
  name = "${var.project_prefix}-lambda-bedrock-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "bedrock:InvokeModel",
        "bedrock:InvokeModelWithResponseStream"
      ]
      Resource = "arn:aws:bedrock:*::foundation-model/*"
    }]
  })
}

# SageMaker access
resource "aws_iam_role_policy" "sagemaker_access" {
  name = "${var.project_prefix}-lambda-sagemaker-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sagemaker:InvokeEndpoint",
          "sagemaker:InvokeEndpointAsync"
        ]
        Resource = "arn:aws:sagemaker:*:*:endpoint/*"
      },
      {
        Effect = "Allow"
        Action = [
          "sagemaker:CreateTrainingJob",
          "sagemaker:DescribeTrainingJob",
          "sagemaker:CreateModel",
          "sagemaker:CreateEndpointConfig",
          "sagemaker:CreateEndpoint",
          "sagemaker:UpdateEndpoint",
          "sagemaker:CreateModelPackage",
          "sagemaker:DescribeModelPackage"
        ]
        Resource = "*"
      }
    ]
  })
}

# IAM PassRole for SageMaker
resource "aws_iam_role_policy" "iam_passrole" {
  name = "${var.project_prefix}-lambda-passrole-policy"
  role = aws_iam_role.lambda_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "iam:PassRole"
      Resource = "*"
      Condition = {
        StringEquals = {
          "iam:PassedToService" = "sagemaker.amazonaws.com"
        }
      }
    }]
  })
}
