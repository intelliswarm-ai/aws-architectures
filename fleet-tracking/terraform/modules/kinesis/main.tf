################################################################################
# Kinesis Data Stream Module
################################################################################

resource "aws_kinesis_stream" "gps_stream" {
  name             = var.stream_name
  shard_count      = var.shard_count
  retention_period = var.retention_period

  shard_level_metrics = [
    "IncomingBytes",
    "IncomingRecords",
    "OutgoingBytes",
    "OutgoingRecords",
    "WriteProvisionedThroughputExceeded",
    "ReadProvisionedThroughputExceeded",
    "IteratorAgeMilliseconds",
  ]

  stream_mode_details {
    stream_mode = var.stream_mode
  }

  encryption_type = "KMS"
  kms_key_id      = var.kms_key_id != "" ? var.kms_key_id : "alias/aws/kinesis"

  tags = merge(var.tags, {
    Name = var.stream_name
  })
}

# CloudWatch Alarm for Iterator Age (Consumer Lag)
resource "aws_cloudwatch_metric_alarm" "iterator_age" {
  alarm_name          = "${var.project_name}-kinesis-iterator-age"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "GetRecords.IteratorAgeMilliseconds"
  namespace           = "AWS/Kinesis"
  period              = 60
  statistic           = "Maximum"
  threshold           = 60000 # 1 minute lag
  alarm_description   = "Kinesis consumer is falling behind"

  dimensions = {
    StreamName = aws_kinesis_stream.gps_stream.name
  }

  tags = var.tags
}

# CloudWatch Alarm for Write Throttling
resource "aws_cloudwatch_metric_alarm" "write_throttled" {
  alarm_name          = "${var.project_name}-kinesis-write-throttled"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "WriteProvisionedThroughputExceeded"
  namespace           = "AWS/Kinesis"
  period              = 60
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Kinesis stream is experiencing write throttling"

  dimensions = {
    StreamName = aws_kinesis_stream.gps_stream.name
  }

  tags = var.tags
}
