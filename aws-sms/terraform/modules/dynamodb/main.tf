################################################################################
# DynamoDB Module - SMS Response Storage
################################################################################

# SMS Responses Table - Stores all inbound SMS responses for 1 year
resource "aws_dynamodb_table" "responses" {
  name           = "${var.project_name}-sms-responses"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "subscriber_id"
  range_key      = "response_timestamp"

  attribute {
    name = "subscriber_id"
    type = "S"
  }

  attribute {
    name = "response_timestamp"
    type = "S"
  }

  attribute {
    name = "campaign_id"
    type = "S"
  }

  attribute {
    name = "response_date"
    type = "S"
  }

  # Global Secondary Index for campaign-based queries
  global_secondary_index {
    name            = "campaign-responses-index"
    hash_key        = "campaign_id"
    range_key       = "response_timestamp"
    projection_type = "ALL"
  }

  # Global Secondary Index for date-based queries
  global_secondary_index {
    name            = "date-responses-index"
    hash_key        = "response_date"
    range_key       = "response_timestamp"
    projection_type = "ALL"
  }

  # TTL for automatic cleanup after 365 days
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name    = "${var.project_name}-sms-responses"
    Purpose = "Store SMS responses for 1 year"
  })
}

# Subscribers Table - Stores subscriber information and preferences
resource "aws_dynamodb_table" "subscribers" {
  name           = "${var.project_name}-subscribers"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "subscriber_id"

  attribute {
    name = "subscriber_id"
    type = "S"
  }

  attribute {
    name = "phone_number"
    type = "S"
  }

  attribute {
    name = "subscription_status"
    type = "S"
  }

  # Global Secondary Index for phone number lookups
  global_secondary_index {
    name            = "phone-number-index"
    hash_key        = "phone_number"
    projection_type = "ALL"
  }

  # Global Secondary Index for status-based queries
  global_secondary_index {
    name            = "status-index"
    hash_key        = "subscription_status"
    projection_type = "KEYS_ONLY"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name    = "${var.project_name}-subscribers"
    Purpose = "Store subscriber information"
  })
}
