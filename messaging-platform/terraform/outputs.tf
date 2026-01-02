################################################################################
# SMS Marketing System - Outputs
################################################################################

output "pinpoint_app_id" {
  description = "Pinpoint application ID"
  value       = module.pinpoint.app_id
}

output "pinpoint_app_arn" {
  description = "Pinpoint application ARN"
  value       = module.pinpoint.app_arn
}

output "kinesis_stream_name" {
  description = "Kinesis stream name"
  value       = module.kinesis.stream_name
}

output "kinesis_stream_arn" {
  description = "Kinesis stream ARN"
  value       = module.kinesis.stream_arn
}

output "kinesis_retention_hours" {
  description = "Kinesis stream retention period in hours"
  value       = module.kinesis.retention_period
}

output "responses_table_name" {
  description = "DynamoDB table for SMS responses"
  value       = module.dynamodb.responses_table_name
}

output "subscribers_table_name" {
  description = "DynamoDB table for subscribers"
  value       = module.dynamodb.subscribers_table_name
}

output "archive_bucket_name" {
  description = "S3 bucket for archived events"
  value       = module.s3.bucket_name
}

output "notifications_topic_arn" {
  description = "SNS topic for notifications"
  value       = module.sns.topic_arn
}

output "event_processor_function_arn" {
  description = "Event processor Lambda function ARN"
  value       = module.lambda.event_processor_function_arn
}

output "response_handler_function_arn" {
  description = "Response handler Lambda function ARN"
  value       = module.lambda.response_handler_function_arn
}

output "analytics_processor_function_arn" {
  description = "Analytics processor Lambda function ARN"
  value       = module.lambda.analytics_processor_function_arn
}

output "archive_consumer_function_arn" {
  description = "Archive consumer Lambda function ARN"
  value       = module.lambda.archive_consumer_function_arn
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.cloudwatch.dashboard_url
}
