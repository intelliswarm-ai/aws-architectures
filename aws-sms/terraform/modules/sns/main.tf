################################################################################
# SNS Module - SMS Notifications
################################################################################

resource "aws_sns_topic" "notifications" {
  name = var.topic_name

  kms_master_key_id = "alias/aws/sns"

  tags = merge(var.tags, {
    Name    = var.topic_name
    Purpose = "SMS marketing notifications"
  })
}

resource "aws_sns_topic_policy" "notifications" {
  arn = aws_sns_topic.notifications.arn

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "${var.topic_name}-policy"
    Statement = [
      {
        Sid    = "AllowLambdaPublish"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.notifications.arn
      },
      {
        Sid    = "AllowPinpointPublish"
        Effect = "Allow"
        Principal = {
          Service = "pinpoint.amazonaws.com"
        }
        Action   = "sns:Publish"
        Resource = aws_sns_topic.notifications.arn
      }
    ]
  })
}
