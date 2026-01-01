variable "environment" {
  type = string
}

variable "name_prefix" {
  type = string
}

variable "transcripts_bucket" {
  type = string
}

variable "output_bucket" {
  type = string
}

variable "retention_days" {
  type    = number
  default = 90
}

variable "enable_versioning" {
  type    = bool
  default = true
}

# Transcripts bucket - input for processing
resource "aws_s3_bucket" "transcripts" {
  bucket = var.transcripts_bucket

  tags = {
    Name = var.transcripts_bucket
  }
}

resource "aws_s3_bucket_versioning" "transcripts" {
  bucket = aws_s3_bucket.transcripts.id
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "transcripts" {
  bucket = aws_s3_bucket.transcripts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "transcripts" {
  bucket = aws_s3_bucket.transcripts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "transcripts" {
  bucket = aws_s3_bucket.transcripts.id

  rule {
    id     = "archive-old-transcripts"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = var.retention_days
      storage_class = "GLACIER"
    }

    expiration {
      days = var.retention_days * 3
    }
  }
}

# Output bucket - Comprehend results
resource "aws_s3_bucket" "output" {
  bucket = var.output_bucket

  tags = {
    Name = var.output_bucket
  }
}

resource "aws_s3_bucket_versioning" "output" {
  bucket = aws_s3_bucket.output.id
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "output" {
  bucket = aws_s3_bucket.output.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "output" {
  bucket = aws_s3_bucket.output.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "output" {
  bucket = aws_s3_bucket.output.id

  rule {
    id     = "cleanup-old-output"
    status = "Enabled"

    expiration {
      days = var.retention_days
    }
  }
}

output "transcripts_bucket_name" {
  value = aws_s3_bucket.transcripts.id
}

output "transcripts_bucket_arn" {
  value = aws_s3_bucket.transcripts.arn
}

output "output_bucket_name" {
  value = aws_s3_bucket.output.id
}

output "output_bucket_arn" {
  value = aws_s3_bucket.output.arn
}
