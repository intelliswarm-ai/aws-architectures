################################################################################
# Outputs
################################################################################

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = aws_apigatewayv2_api.main.api_endpoint
}

output "alb_dns_name" {
  description = "Application Load Balancer DNS name"
  value       = module.ec2.alb_dns_name
}

output "sqs_queue_url" {
  description = "URL of the transaction queue"
  value       = module.sqs.queue_url
}

output "sqs_dlq_url" {
  description = "URL of the dead letter queue"
  value       = module.sqs.dlq_url
}

output "asg_name" {
  description = "Name of the Auto Scaling Group"
  value       = module.ec2.asg_name
}

output "cloudwatch_dashboard" {
  description = "CloudWatch dashboard name"
  value       = module.cloudwatch.dashboard_name
}

output "transactions_table_name" {
  description = "DynamoDB transactions table name"
  value       = aws_dynamodb_table.transactions.name
}

output "s3_bucket" {
  description = "S3 bucket for deployment artifacts"
  value       = module.s3.bucket_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "lambda_api_function" {
  description = "API Lambda function name"
  value       = aws_lambda_function.api.function_name
}
