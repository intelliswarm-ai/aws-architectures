################################################################################
# GPS Tracking System - Outputs
################################################################################

# Kinesis Outputs
output "kinesis_stream_name" {
  description = "Name of the Kinesis data stream"
  value       = module.kinesis.stream_name
}

output "kinesis_stream_arn" {
  description = "ARN of the Kinesis data stream"
  value       = module.kinesis.stream_arn
}

# DynamoDB Outputs
output "positions_table_name" {
  description = "Name of the truck positions DynamoDB table"
  value       = module.dynamodb.positions_table_name
}

output "geofences_table_name" {
  description = "Name of the geofences DynamoDB table"
  value       = module.dynamodb.geofences_table_name
}

# S3 Outputs
output "archive_bucket_name" {
  description = "Name of the S3 archive bucket"
  value       = module.s3.bucket_name
}

output "archive_bucket_arn" {
  description = "ARN of the S3 archive bucket"
  value       = module.s3.bucket_arn
}

# SNS Outputs
output "alerts_topic_arn" {
  description = "ARN of the geofence alerts SNS topic"
  value       = module.sns.topic_arn
}

# Lambda Outputs
output "producer_function_name" {
  description = "Name of the GPS producer Lambda function"
  value       = module.lambda.producer_function_name
}

output "dashboard_consumer_function_name" {
  description = "Name of the dashboard consumer Lambda function"
  value       = module.lambda.dashboard_consumer_function_name
}

output "geofence_consumer_function_name" {
  description = "Name of the geofence consumer Lambda function"
  value       = module.lambda.geofence_consumer_function_name
}

output "archive_consumer_function_name" {
  description = "Name of the archive consumer Lambda function"
  value       = module.lambda.archive_consumer_function_name
}

# CloudWatch Dashboard
output "cloudwatch_dashboard_url" {
  description = "URL to the CloudWatch dashboard"
  value       = module.cloudwatch.dashboard_url
}

# Useful Commands
output "useful_commands" {
  description = "Useful AWS CLI commands for testing"
  value = {
    invoke_producer  = "aws lambda invoke --function-name ${module.lambda.producer_function_name} --payload '{}' response.json"
    list_trucks      = "aws dynamodb scan --table-name ${module.dynamodb.positions_table_name}"
    view_stream      = "aws kinesis describe-stream --stream-name ${module.kinesis.stream_name}"
    get_shard_iterator = "aws kinesis get-shard-iterator --stream-name ${module.kinesis.stream_name} --shard-id shardId-000000000000 --shard-iterator-type LATEST"
  }
}
