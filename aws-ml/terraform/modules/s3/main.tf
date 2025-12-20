# S3 Buckets for ML Platform

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

locals {
  raw_bucket_name       = var.raw_bucket_name != "" ? var.raw_bucket_name : "${var.project_prefix}-raw-${random_id.bucket_suffix.hex}"
  processed_bucket_name = var.processed_bucket_name != "" ? var.processed_bucket_name : "${var.project_prefix}-processed-${random_id.bucket_suffix.hex}"
  model_bucket_name     = var.model_bucket_name != "" ? var.model_bucket_name : "${var.project_prefix}-models-${random_id.bucket_suffix.hex}"
}

# Raw Documents Bucket
resource "aws_s3_bucket" "raw" {
  bucket = local.raw_bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Processed Documents Bucket
resource "aws_s3_bucket" "processed" {
  bucket = local.processed_bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "processed" {
  bucket = aws_s3_bucket.processed.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed" {
  bucket = aws_s3_bucket.processed.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "processed" {
  bucket                  = aws_s3_bucket.processed.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Model Artifacts Bucket
resource "aws_s3_bucket" "models" {
  bucket = local.model_bucket_name
  tags   = var.tags
}

resource "aws_s3_bucket_versioning" "models" {
  bucket = aws_s3_bucket.models.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "models" {
  bucket = aws_s3_bucket.models.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "models" {
  bucket                  = aws_s3_bucket.models.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
