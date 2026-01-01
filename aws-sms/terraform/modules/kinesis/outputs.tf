################################################################################
# Kinesis Module - Outputs
################################################################################

output "stream_name" {
  description = "Name of the Kinesis stream"
  value       = aws_kinesis_stream.sms_events.name
}

output "stream_arn" {
  description = "ARN of the Kinesis stream"
  value       = aws_kinesis_stream.sms_events.arn
}

output "retention_period" {
  description = "Retention period in hours"
  value       = aws_kinesis_stream.sms_events.retention_period
}

output "shard_count" {
  description = "Number of shards"
  value       = aws_kinesis_stream.sms_events.shard_count
}
