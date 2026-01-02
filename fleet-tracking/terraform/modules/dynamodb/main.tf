################################################################################
# DynamoDB Tables Module
################################################################################

# Truck Positions Table - Stores latest position for each truck
resource "aws_dynamodb_table" "positions" {
  name         = "${var.project_name}-truck-positions"
  billing_mode = var.billing_mode
  hash_key     = "truck_id"

  # Provisioned capacity (only used if billing_mode is PROVISIONED)
  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null

  attribute {
    name = "truck_id"
    type = "S"
  }

  # TTL for automatic cleanup
  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  # Point-in-time recovery for production
  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  # Server-side encryption
  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-truck-positions"
  })
}

# Geofences Table - Stores geofence definitions
resource "aws_dynamodb_table" "geofences" {
  name         = "${var.project_name}-geofences"
  billing_mode = var.billing_mode
  hash_key     = "geofence_id"

  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null

  attribute {
    name = "geofence_id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-geofences"
  })
}

# Global Secondary Index for querying positions by last_update
resource "aws_dynamodb_table" "position_history" {
  count = var.enable_history_table ? 1 : 0

  name         = "${var.project_name}-position-history"
  billing_mode = var.billing_mode
  hash_key     = "truck_id"
  range_key    = "timestamp"

  read_capacity  = var.billing_mode == "PROVISIONED" ? var.read_capacity : null
  write_capacity = var.billing_mode == "PROVISIONED" ? var.write_capacity : null

  attribute {
    name = "truck_id"
    type = "S"
  }

  attribute {
    name = "timestamp"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "${var.project_name}-position-history"
  })
}
