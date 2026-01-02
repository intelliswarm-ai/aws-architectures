################################################################################
# CloudWatch Module Outputs
################################################################################

output "processor_log_group_name" {
  description = "Name of the processor log group"
  value       = aws_cloudwatch_log_group.processor.name
}

output "processor_log_group_arn" {
  description = "ARN of the processor log group"
  value       = aws_cloudwatch_log_group.processor.arn
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "high_queue_depth_alarm_arn" {
  description = "ARN of the high queue depth alarm"
  value       = aws_cloudwatch_metric_alarm.high_queue_depth.arn
}

output "dlq_alarm_arn" {
  description = "ARN of the DLQ alarm"
  value       = aws_cloudwatch_metric_alarm.dlq_messages.arn
}
