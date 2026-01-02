output "stream_name" {
  description = "Name of the Kinesis stream"
  value       = aws_kinesis_stream.gps_stream.name
}

output "stream_arn" {
  description = "ARN of the Kinesis stream"
  value       = aws_kinesis_stream.gps_stream.arn
}

output "shard_count" {
  description = "Number of shards"
  value       = aws_kinesis_stream.gps_stream.shard_count
}
