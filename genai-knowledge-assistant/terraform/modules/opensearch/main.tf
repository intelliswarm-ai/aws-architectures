# =============================================================================
# OpenSearch Serverless Module - Vector Store
# =============================================================================

# =============================================================================
# Security Policy - Network
# =============================================================================

resource "aws_opensearchserverless_security_policy" "network" {
  name = "${var.project_prefix}-network"
  type = "network"

  policy = jsonencode([
    {
      Description = "Public access for ${var.project_prefix}"
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/${var.collection_name}"]
        },
        {
          ResourceType = "dashboard"
          Resource     = ["collection/${var.collection_name}"]
        }
      ]
      AllowFromPublic = true
    }
  ])
}

# =============================================================================
# Security Policy - Encryption
# =============================================================================

resource "aws_opensearchserverless_security_policy" "encryption" {
  name = "${var.project_prefix}-encryption"
  type = "encryption"

  policy = jsonencode({
    Rules = [
      {
        ResourceType = "collection"
        Resource     = ["collection/${var.collection_name}"]
      }
    ]
    AWSOwnedKey = true
  })
}

# =============================================================================
# Collection
# =============================================================================

resource "aws_opensearchserverless_collection" "vectors" {
  name             = var.collection_name
  type             = "VECTORSEARCH"
  standby_replicas = var.standby_replicas

  depends_on = [
    aws_opensearchserverless_security_policy.network,
    aws_opensearchserverless_security_policy.encryption
  ]

  tags = merge(var.tags, {
    Name = var.collection_name
  })
}

# =============================================================================
# Access Policy
# =============================================================================

data "aws_caller_identity" "current" {}

resource "aws_opensearchserverless_access_policy" "vectors" {
  name = "${var.project_prefix}-access"
  type = "data"

  policy = jsonencode([
    {
      Description = "Access for ${var.project_prefix}"
      Rules = [
        {
          ResourceType = "collection"
          Resource     = ["collection/${var.collection_name}"]
          Permission = [
            "aoss:CreateCollectionItems",
            "aoss:DeleteCollectionItems",
            "aoss:UpdateCollectionItems",
            "aoss:DescribeCollectionItems"
          ]
        },
        {
          ResourceType = "index"
          Resource     = ["index/${var.collection_name}/*"]
          Permission = [
            "aoss:CreateIndex",
            "aoss:DeleteIndex",
            "aoss:UpdateIndex",
            "aoss:DescribeIndex",
            "aoss:ReadDocument",
            "aoss:WriteDocument"
          ]
        }
      ]
      Principal = [
        "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
      ]
    }
  ])
}
