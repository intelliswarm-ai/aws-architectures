# =============================================================================
# Security Groups Module
# =============================================================================

# -----------------------------------------------------------------------------
# Lambda Security Group
# -----------------------------------------------------------------------------

resource "aws_security_group" "lambda" {
  name        = "${var.name_prefix}-lambda-sg"
  description = "Security group for Lambda functions in VPC"
  vpc_id      = var.vpc_id

  # Allow all outbound traffic (required for Lambda to call AWS services)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-lambda-sg"
  })
}

# -----------------------------------------------------------------------------
# VPC Endpoints Security Group
# -----------------------------------------------------------------------------

resource "aws_security_group" "vpc_endpoints" {
  name        = "${var.name_prefix}-vpce-sg"
  description = "Security group for VPC endpoints"
  vpc_id      = var.vpc_id

  # Allow HTTPS from VPC
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
    description = "Allow HTTPS from VPC"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-vpce-sg"
  })
}

# -----------------------------------------------------------------------------
# Database Security Group (Optional)
# -----------------------------------------------------------------------------

resource "aws_security_group" "database" {
  count = var.create_database_sg ? 1 : 0

  name        = "${var.name_prefix}-database-sg"
  description = "Security group for RDS database"
  vpc_id      = var.vpc_id

  # Allow traffic from Lambda
  ingress {
    from_port       = var.database_port
    to_port         = var.database_port
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
    description     = "Allow from Lambda"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-database-sg"
  })
}

# -----------------------------------------------------------------------------
# Cache Security Group (Optional)
# -----------------------------------------------------------------------------

resource "aws_security_group" "cache" {
  count = var.create_cache_sg ? 1 : 0

  name        = "${var.name_prefix}-cache-sg"
  description = "Security group for ElastiCache"
  vpc_id      = var.vpc_id

  # Allow Redis traffic from Lambda
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.lambda.id]
    description     = "Allow Redis from Lambda"
  }

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-cache-sg"
  })
}
