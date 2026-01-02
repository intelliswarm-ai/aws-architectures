################################################################################
# Kinesis Data Stream Module - 365 Day Retention
################################################################################

resource "aws_kinesis_stream" "sms_events" {
  name             = var.stream_name
  shard_count      = var.shard_count
  retention_period = var.retention_period  # 8760 hours = 365 days

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
  kms_key_id      = "alias/aws/kinesis"

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "WriteProvisionedThroughputExceeded",
    "ReadProvisionedThroughputExceeded",
    "IteratorAgeMilliseconds",
  ]

  tags = merge(var.tags, {
    Name            = var.stream_name
    RetentionDays   = var.retention_period / 24
    Purpose         = "SMS event collection and analysis"
  })
}

# CloudWatch Alarm for Iterator Age (consumer lag)
resource "aws_cloudwatch_metric_alarm" "iterator_age" {
  alarm_name          = "${var.project_name}-kinesis-iterator-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  namespace           = "AWS/Kinesis"
  period              = 300
  statistic           = "Maximum"
  threshold           = 60000  # 60 seconds
  alarm_description   = "Kinesis consumer lag is too high"

  dimensions = {
    StreamName = aws_kinesis_stream.sms_events.name
  }

  tags = var.tags
}

# CloudWatch Alarm for Write Throttling
resource "aws_cloudwatch_metric_alarm" "write_throttling" {
  alarm_name          = "${var.project_name}-kinesis-write-throttling"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "WriteProvisionedThroughputExceeded"
  namespace           = "AWS/Kinesis"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Kinesis write throttling detected"

  dimensions = {
    StreamName = aws_kinesis_stream.sms_events.name
  }

  tags = var.tags
}
