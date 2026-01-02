# Step Functions State Machine
resource "aws_sfn_state_machine" "task_workflow" {
  name     = var.state_machine_name
  role_arn = aws_iam_role.sfn_exec.arn

  definition = templatefile("${path.module}/definitions/task-workflow.asl.json", {
    validate_task_lambda_arn = var.validate_task_lambda_arn
    process_task_lambda_arn  = var.process_task_lambda_arn
    finalize_task_lambda_arn = var.finalize_task_lambda_arn
    success_topic_arn        = var.success_topic_arn
    failure_topic_arn        = var.failure_topic_arn
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn_logs.arn}:*"
    include_execution_data = true
    level                  = var.log_level
  }

  tracing_configuration {
    enabled = var.enable_xray
  }

  tags = var.tags
}

# CloudWatch Log Group for Step Functions
resource "aws_cloudwatch_log_group" "sfn_logs" {
  name              = "/aws/vendedlogs/states/${var.state_machine_name}"
  retention_in_days = var.log_retention_days
  tags              = var.tags
}

# IAM Role for Step Functions
resource "aws_iam_role" "sfn_exec" {
  name = "${var.state_machine_name}-sfn-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = var.tags
}

# Policy to invoke Lambda functions
resource "aws_iam_role_policy" "sfn_lambda" {
  name = "${var.state_machine_name}-lambda-policy"
  role = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          var.validate_task_lambda_arn,
          var.process_task_lambda_arn,
          var.finalize_task_lambda_arn,
          "${var.validate_task_lambda_arn}:*",
          "${var.process_task_lambda_arn}:*",
          "${var.finalize_task_lambda_arn}:*"
        ]
      }
    ]
  })
}

# Policy to publish to SNS
resource "aws_iam_role_policy" "sfn_sns" {
  name = "${var.state_machine_name}-sns-policy"
  role = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "sns:Publish"
        ]
        Resource = [
          var.success_topic_arn,
          var.failure_topic_arn
        ]
      }
    ]
  })
}

# Policy to write CloudWatch Logs
resource "aws_iam_role_policy" "sfn_logs" {
  name = "${var.state_machine_name}-logs-policy"
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

# X-Ray tracing policy
resource "aws_iam_role_policy" "sfn_xray" {
  count = var.enable_xray ? 1 : 0
  name  = "${var.state_machine_name}-xray-policy"
  role  = aws_iam_role.sfn_exec.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ]
        Resource = "*"
      }
    ]
  })
}
