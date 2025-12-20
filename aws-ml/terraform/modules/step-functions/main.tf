# Step Functions for Document Processing Workflow

resource "aws_sfn_state_machine" "document_workflow" {
  name     = "${var.project_prefix}-document-processing"
  role_arn = aws_iam_role.sfn_exec.arn

  definition = jsonencode({
    Comment = "Intelligent Document Processing Pipeline"
    StartAt = "ValidateDocument"
    States = {
      ValidateDocument = {
        Type     = "Task"
        Resource = var.validate_lambda_arn
        Parameters = {
          "document_id.$"   = "$.document_id"
          "bucket.$"        = "$.bucket"
          "key.$"           = "$.key"
          "document_type.$" = "$.document_type"
          "handler_type"    = "validate"
        }
        ResultPath = "$"
        Next       = "RouteByType"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "NotifyFailure"
        }]
      }

      RouteByType = {
        Type    = "Choice"
        Choices = [
          {
            Variable      = "$.document_type"
            StringEquals  = "AUDIO"
            Next          = "TranscribeAudio"
          },
          {
            Variable      = "$.document_type"
            StringEquals  = "IMAGE"
            Next          = "ProcessImage"
          }
        ]
        Default = "ExtractText"
      }

      ExtractText = {
        Type     = "Task"
        Resource = var.extraction_lambda_arn
        ResultPath = "$"
        Next     = "AnalyzeContent"
        Retry = [{
          ErrorEquals     = ["RetryableError"]
          IntervalSeconds = 30
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "NotifyFailure"
        }]
      }

      TranscribeAudio = {
        Type     = "Task"
        Resource = var.transcription_lambda_arn
        ResultPath = "$"
        Next     = "AnalyzeContent"
        Retry = [{
          ErrorEquals     = ["RetryableError"]
          IntervalSeconds = 60
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "NotifyFailure"
        }]
      }

      ProcessImage = {
        Type     = "Parallel"
        Branches = [
          {
            StartAt = "ExtractImageText"
            States = {
              ExtractImageText = {
                Type     = "Task"
                Resource = var.extraction_lambda_arn
                End      = true
              }
            }
          },
          {
            StartAt = "AnalyzeImage"
            States = {
              AnalyzeImage = {
                Type     = "Task"
                Resource = var.analysis_lambda_arn
                Parameters = {
                  "document_id.$"   = "$.document_id"
                  "bucket.$"        = "$.bucket"
                  "key.$"           = "$.key"
                  "document_type.$" = "$.document_type"
                  "extraction"      = {}
                }
                End = true
              }
            }
          }
        ]
        ResultPath = "$.parallel_results"
        Next       = "AggregateResults"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "NotifyFailure"
        }]
      }

      AggregateResults = {
        Type     = "Task"
        Resource = var.validate_lambda_arn
        Parameters = {
          "handler_type" = "aggregate"
          "results.$"    = "$.parallel_results"
          "document_id.$" = "$.document_id"
        }
        ResultPath = "$"
        Next       = "ClassifyDocument"
      }

      AnalyzeContent = {
        Type     = "Task"
        Resource = var.analysis_lambda_arn
        ResultPath = "$"
        Next     = "ClassifyDocument"
        Retry = [{
          ErrorEquals     = ["RetryableError"]
          IntervalSeconds = 10
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "NotifyFailure"
        }]
      }

      ClassifyDocument = {
        Type     = "Task"
        Resource = var.inference_lambda_arn
        ResultPath = "$"
        Next     = "GenerateInsights"
        Retry = [{
          ErrorEquals     = ["RetryableError"]
          IntervalSeconds = 5
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "NotifyFailure"
        }]
      }

      GenerateInsights = {
        Type     = "Task"
        Resource = var.bedrock_lambda_arn
        ResultPath = "$"
        Next     = "FinalizeProcessing"
        Retry = [{
          ErrorEquals     = ["RetryableError"]
          IntervalSeconds = 10
          MaxAttempts     = 3
          BackoffRate     = 2
        }]
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "NotifyFailure"
        }]
      }

      FinalizeProcessing = {
        Type     = "Task"
        Resource = var.finalize_lambda_arn
        Parameters = {
          "handler_type" = "finalize"
          "document_id.$" = "$.document_id"
          "extraction.$"  = "$.extraction"
          "analysis.$"    = "$.analysis"
          "inference.$"   = "$.inference"
          "generation.$"  = "$.generation"
        }
        ResultPath = "$"
        Next       = "NotifySuccess"
        Catch = [{
          ErrorEquals = ["States.ALL"]
          ResultPath  = "$.error"
          Next        = "NotifyFailure"
        }]
      }

      NotifySuccess = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn   = var.success_topic_arn
          "Message.$" = "States.JsonToString($)"
          Subject    = "Document Processing Complete"
        }
        End = true
      }

      NotifyFailure = {
        Type     = "Task"
        Resource = "arn:aws:states:::sns:publish"
        Parameters = {
          TopicArn   = var.failure_topic_arn
          "Message.$" = "States.JsonToString($)"
          Subject    = "Document Processing Failed"
        }
        End = true
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn_logs.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  tracing_configuration {
    enabled = true
  }

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "sfn_logs" {
  name              = "/aws/vendedlogs/states/${var.project_prefix}-document-processing"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# IAM Role for Step Functions
resource "aws_iam_role" "sfn_exec" {
  name = "${var.project_prefix}-sfn-exec-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "states.amazonaws.com"
      }
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "sfn_lambda" {
  name = "${var.project_prefix}-sfn-lambda-policy"
  role = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["lambda:InvokeFunction"]
      Resource = [
        var.validate_lambda_arn,
        var.route_lambda_arn,
        var.extraction_lambda_arn,
        var.transcription_lambda_arn,
        var.analysis_lambda_arn,
        var.inference_lambda_arn,
        var.bedrock_lambda_arn,
        var.finalize_lambda_arn,
        "${var.validate_lambda_arn}:*",
        "${var.route_lambda_arn}:*",
        "${var.extraction_lambda_arn}:*",
        "${var.transcription_lambda_arn}:*",
        "${var.analysis_lambda_arn}:*",
        "${var.inference_lambda_arn}:*",
        "${var.bedrock_lambda_arn}:*",
        "${var.finalize_lambda_arn}:*",
      ]
    }]
  })
}

resource "aws_iam_role_policy" "sfn_sns" {
  name = "${var.project_prefix}-sfn-sns-policy"
  role = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["sns:Publish"]
      Resource = [var.success_topic_arn, var.failure_topic_arn]
    }]
  })
}

resource "aws_iam_role_policy" "sfn_logs" {
  name = "${var.project_prefix}-sfn-logs-policy"
  role = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy" "sfn_xray" {
  name = "${var.project_prefix}-sfn-xray-policy"
  role = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "xray:PutTraceSegments",
        "xray:PutTelemetryRecords",
        "xray:GetSamplingRules",
        "xray:GetSamplingTargets"
      ]
      Resource = "*"
    }]
  })
}
