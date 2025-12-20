# =============================================================================
# DynamoDB Module
# =============================================================================

resource "aws_dynamodb_table" "main" {
  name         = "${var.name_prefix}-${var.table_name}"
  billing_mode = var.billing_mode
  hash_key     = var.hash_key
  range_key    = var.range_key

  attribute {
    name = var.hash_key
    type = "S"
  }

  dynamic "attribute" {
    for_each = var.range_key != null ? [var.range_key] : []
    content {
      name = attribute.value
      type = "S"
    }
  }

  dynamic "attribute" {
    for_each = var.global_secondary_indexes
    content {
      name = attribute.value.hash_key
      type = "S"
    }
  }

  dynamic "attribute" {
    for_each = [for gsi in var.global_secondary_indexes : gsi.range_key if gsi.range_key != null]
    content {
      name = attribute.value
      type = "S"
    }
  }

  dynamic "global_secondary_index" {
    for_each = var.global_secondary_indexes
    content {
      name            = global_secondary_index.value.name
      hash_key        = global_secondary_index.value.hash_key
      range_key       = lookup(global_secondary_index.value, "range_key", null)
      projection_type = "ALL"
    }
  }

  dynamic "ttl" {
    for_each = var.enable_ttl ? [1] : []
    content {
      attribute_name = var.ttl_attribute
      enabled        = true
    }
  }

  point_in_time_recovery {
    enabled = var.enable_pitr
  }

  server_side_encryption {
    enabled     = var.kms_key_arn != null
    kms_key_arn = var.kms_key_arn
  }

  tags = var.tags
}
