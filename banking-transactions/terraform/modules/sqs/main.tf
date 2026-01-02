################################################################################
# SQS Module - Transaction Queue with Dead Letter Queue
################################################################################

# Dead Letter Queue
resource "aws_sqs_queue" "dlq" {
  name                      = "${var.project_name}-transactions-dlq"
  message_retention_seconds = var.dlq_retention_seconds
  receive_wait_time_seconds = 20

  # Enable server-side encryption
  sqs_managed_sse_enabled = true

  tags = merge(var.tags, {
    Name = "${var.project_name}-transactions-dlq"
    Type = "DeadLetterQueue"
  })
}

# Main Transaction Queue
resource "aws_sqs_queue" "main" {
  name                       = "${var.project_name}-transactions"
  visibility_timeout_seconds = var.visibility_timeout
  message_retention_seconds  = var.message_retention_seconds
  receive_wait_time_seconds  = 20  # Long polling
  delay_seconds              = 0

  # Enable server-side encryption
  sqs_managed_sse_enabled = true

  # Dead letter queue configuration
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = merge(var.tags, {
    Name = "${var.project_name}-transactions"
    Type = "MainQueue"
  })
}

# Allow DLQ to receive messages from main queue
resource "aws_sqs_queue_redrive_allow_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id

  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.main.arn]
  })
}

# Queue Policy - Allow Lambda to send messages
resource "aws_sqs_queue_policy" "main" {
  queue_url = aws_sqs_queue.main.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowLambdaSendMessage"
        Effect    = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action    = "sqs:SendMessage"
        Resource  = aws_sqs_queue.main.arn
        Condition = {
          ArnLike = {
            "aws:SourceArn" = "arn:aws:lambda:${var.aws_region}:${var.account_id}:function:${var.project_name}-*"
          }
        }
      },
      {
        Sid       = "AllowEC2ReceiveMessage"
        Effect    = "Allow"
        Principal = {
          AWS = var.ec2_role_arn
        }
        Action = [
          "sqs:ReceiveMessage",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:ChangeMessageVisibility"
        ]
        Resource = aws_sqs_queue.main.arn
      }
    ]
  })
}
