# =============================================================================
# Bedrock Module - Knowledge Base & Agent
# =============================================================================

# =============================================================================
# Knowledge Base
# =============================================================================

resource "aws_bedrockagent_knowledge_base" "main" {
  name     = "${var.project_prefix}-knowledge-base"
  role_arn = aws_iam_role.knowledge_base.arn

  knowledge_base_configuration {
    type = "VECTOR"
    vector_knowledge_base_configuration {
      embedding_model_arn = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.embedding_model_id}"
    }
  }

  storage_configuration {
    type = "OPENSEARCH_SERVERLESS"
    opensearch_serverless_configuration {
      collection_arn    = var.opensearch_collection_arn
      vector_index_name = "knowledge-index"
      field_mapping {
        vector_field   = "embedding"
        text_field     = "content"
        metadata_field = "metadata"
      }
    }
  }

  tags = var.tags
}

# =============================================================================
# Knowledge Base Data Source
# =============================================================================

resource "aws_bedrockagent_data_source" "s3" {
  name                 = "${var.project_prefix}-s3-source"
  knowledge_base_id    = aws_bedrockagent_knowledge_base.main.id
  data_deletion_policy = "DELETE"

  data_source_configuration {
    type = "S3"
    s3_configuration {
      bucket_arn = var.documents_bucket_arn
    }
  }

  vector_ingestion_configuration {
    chunking_configuration {
      chunking_strategy = "FIXED_SIZE"
      fixed_size_chunking_configuration {
        max_tokens         = var.chunk_size
        overlap_percentage = (var.chunk_overlap * 100) / var.chunk_size
      }
    }
  }
}

# =============================================================================
# Knowledge Base IAM Role
# =============================================================================

resource "aws_iam_role" "knowledge_base" {
  name = "${var.project_prefix}-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = var.account_id
          }
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "knowledge_base" {
  name = "${var.project_prefix}-kb-policy"
  role = aws_iam_role.knowledge_base.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.documents_bucket_arn,
          "${var.documents_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "aoss:APIAccessAll"
        ]
        Resource = var.opensearch_collection_arn
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.embedding_model_id}"
      }
    ]
  })
}

# =============================================================================
# Bedrock Agent (Conditional)
# =============================================================================

resource "aws_bedrockagent_agent" "main" {
  count = var.create_agent ? 1 : 0

  agent_name              = "${var.project_prefix}-agent"
  agent_resource_role_arn = aws_iam_role.agent[0].arn
  foundation_model        = var.foundation_model_id
  idle_session_ttl_in_seconds = 600

  instruction = <<-EOT
    You are a helpful knowledge assistant. Your role is to answer questions based on
    the documents in the knowledge base. Follow these guidelines:

    1. Base your answers on the information retrieved from the knowledge base
    2. If you cannot find relevant information, say so clearly
    3. Cite your sources when possible
    4. Be concise but thorough in your responses
    5. If asked about topics outside the knowledge base, politely redirect
  EOT

  tags = var.tags
}

resource "aws_bedrockagent_agent_knowledge_base_association" "main" {
  count = var.create_agent ? 1 : 0

  agent_id             = aws_bedrockagent_agent.main[0].id
  knowledge_base_id    = aws_bedrockagent_knowledge_base.main.id
  knowledge_base_state = "ENABLED"
  description          = "Knowledge base for document Q&A"
}

resource "aws_bedrockagent_agent_alias" "main" {
  count = var.create_agent ? 1 : 0

  agent_alias_name = "production"
  agent_id         = aws_bedrockagent_agent.main[0].id
  description      = "Production alias"

  tags = var.tags
}

# =============================================================================
# Agent IAM Role
# =============================================================================

resource "aws_iam_role" "agent" {
  count = var.create_agent ? 1 : 0

  name = "${var.project_prefix}-agent-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = var.account_id
          }
        }
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "agent" {
  count = var.create_agent ? 1 : 0

  name = "${var.project_prefix}-agent-policy"
  role = aws_iam_role.agent[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream"
        ]
        Resource = "arn:aws:bedrock:${var.aws_region}::foundation-model/${var.foundation_model_id}"
      },
      {
        Effect = "Allow"
        Action = [
          "bedrock:Retrieve"
        ]
        Resource = aws_bedrockagent_knowledge_base.main.arn
      }
    ]
  })
}
