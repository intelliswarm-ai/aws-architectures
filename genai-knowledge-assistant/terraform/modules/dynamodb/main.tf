# =============================================================================
# DynamoDB Module - Document & Conversation Storage
# =============================================================================

# =============================================================================
# Documents Table
# =============================================================================

resource "aws_dynamodb_table" "documents" {
  name         = "${var.project_prefix}-documents"
  billing_mode = var.environment == "prod" ? "PROVISIONED" : "PAY_PER_REQUEST"
  hash_key     = "documentId"

  # Provisioned capacity for production
  dynamic "provisioned_throughput" {
    for_each = var.environment == "prod" ? [1] : []
    content {
      read_capacity  = 10
      write_capacity = 10
    }
  }

  attribute {
    name = "documentId"
    type = "S"
  }

  attribute {
    name = "knowledgeBaseId"
    type = "S"
  }

  attribute {
    name = "status"
    type = "S"
  }

  # GSI for querying by knowledge base
  global_secondary_index {
    name            = "knowledgeBaseId-index"
    hash_key        = "knowledgeBaseId"
    range_key       = "documentId"
    projection_type = "ALL"

    dynamic "provisioned_throughput" {
      for_each = var.environment == "prod" ? [1] : []
      content {
        read_capacity  = 5
        write_capacity = 5
      }
    }
  }

  # GSI for querying by status
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    range_key       = "documentId"
    projection_type = "KEYS_ONLY"

    dynamic "provisioned_throughput" {
      for_each = var.environment == "prod" ? [1] : []
      content {
        read_capacity  = 5
        write_capacity = 5
      }
    }
  }

  point_in_time_recovery {
    enabled = var.environment == "prod"
  }

  server_side_encryption {
    enabled = true
  }

  tags = merge(var.tags, {
    Name = "${var.project_prefix}-documents"
  })
}

# =============================================================================
# Conversations Table
# =============================================================================

resource "aws_dynamodb_table" "conversations" {
  name         = "${var.project_prefix}-conversations"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "conversationId"

  attribute {
    name = "conversationId"
    type = "S"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  # GSI for querying by user
  global_secondary_index {
    name            = "userId-index"
    hash_key        = "userId"
    range_key       = "conversationId"
    projection_type = "ALL"
  }

  # TTL for automatic conversation expiry
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
    Name = "${var.project_prefix}-conversations"
  })
}
