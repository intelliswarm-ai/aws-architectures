output "task_queue_url" {
  description = "URL of the main task SQS queue"
  value       = module.sqs.queue_url
}

output "task_queue_arn" {
  description = "ARN of the main task SQS queue"
  value       = module.sqs.queue_arn
}

output "dlq_url" {
  description = "URL of the dead letter queue"
  value       = module.sqs.dlq_url
}

output "task_table_name" {
  description = "Name of the DynamoDB task state table"
  value       = module.dynamodb.table_name
}

output "task_table_arn" {
  description = "ARN of the DynamoDB task state table"
  value       = module.dynamodb.table_arn
}

output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = module.step_functions.state_machine_arn
}

output "state_machine_name" {
  description = "Name of the Step Functions state machine"
  value       = module.step_functions.state_machine_name
}

output "success_topic_arn" {
  description = "ARN of the success notification SNS topic"
  value       = module.sns.success_topic_arn
}

output "failure_topic_arn" {
  description = "ARN of the failure notification SNS topic"
  value       = module.sns.failure_topic_arn
}

output "lambda_functions" {
  description = "Map of Lambda function names to ARNs"
  value = {
    task_generator = module.lambda_task_generator.function_arn
    task_worker    = module.lambda_task_worker.function_arn
    validate_task  = module.lambda_validate_task.function_arn
    process_task   = module.lambda_process_task.function_arn
    finalize_task  = module.lambda_finalize_task.function_arn
    notification   = module.lambda_notification.function_arn
  }
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge scheduled rule"
  value       = module.eventbridge.rule_arn
}

output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = "https://${var.aws_region}.console.aws.amazon.com/cloudwatch/home?region=${var.aws_region}#dashboards:name=${module.cloudwatch.dashboard_name}"
}
