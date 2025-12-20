# =============================================================================
# Secrets Manager Module - Secrets with Rotation Support
# =============================================================================

locals {
  prefix = "${var.project_name}-${var.environment}"

  common_tags = merge(var.tags, {
    Module      = "secrets-manager"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# Application Secrets
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "this" {
  for_each = var.secrets

  name        = "${local.prefix}/${each.key}"
  description = each.value.description
  kms_key_id  = var.kms_key_arn

  recovery_window_in_days = each.value.recovery_days

  tags = merge(local.common_tags, {
    SecretName = each.key
  })
}

resource "aws_secretsmanager_secret_version" "this" {
  for_each = var.secrets

  secret_id     = aws_secretsmanager_secret.this[each.key].id
  secret_string = each.value.secret_string
  secret_binary = each.value.secret_binary

  lifecycle {
    ignore_changes = [
      secret_string,
      secret_binary
    ]
  }
}

# -----------------------------------------------------------------------------
# Secret Rotation
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret_rotation" "this" {
  for_each = { for k, v in var.secrets : k => v if v.enable_rotation && v.rotation_lambda_arn != null }

  secret_id           = aws_secretsmanager_secret.this[each.key].id
  rotation_lambda_arn = each.value.rotation_lambda_arn

  rotation_rules {
    automatically_after_days = each.value.rotation_days
  }
}

# -----------------------------------------------------------------------------
# Tenant-Specific Secrets (Templates)
# -----------------------------------------------------------------------------
resource "aws_secretsmanager_secret" "tenant" {
  for_each = var.tenant_secrets

  name        = "${local.prefix}/tenants/${each.key}"
  description = each.value.description
  kms_key_id  = var.kms_key_arn

  recovery_window_in_days = 7

  tags = merge(local.common_tags, {
    SecretName = each.key
    TenantSecret = "true"
  })
}

resource "aws_secretsmanager_secret_version" "tenant" {
  for_each = var.tenant_secrets

  secret_id     = aws_secretsmanager_secret.tenant[each.key].id
  secret_string = jsonencode(each.value.template)

  lifecycle {
    ignore_changes = [
      secret_string
    ]
  }
}

# -----------------------------------------------------------------------------
# Default Secrets for Multi-Tenant SaaS Platform
# -----------------------------------------------------------------------------
# Database credentials secret
resource "aws_secretsmanager_secret" "database" {
  name        = "${local.prefix}/database/credentials"
  description = "Database credentials for the platform"
  kms_key_id  = var.kms_key_arn

  recovery_window_in_days = 7

  tags = merge(local.common_tags, {
    SecretType = "database"
  })
}

resource "aws_secretsmanager_secret_version" "database" {
  secret_id = aws_secretsmanager_secret.database.id
  secret_string = jsonencode({
    username = "admin"
    password = "CHANGE_ME_BEFORE_PRODUCTION"
    host     = "localhost"
    port     = 5432
    database = "${var.project_name}_${var.environment}"
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# API integration secrets
resource "aws_secretsmanager_secret" "api_integrations" {
  name        = "${local.prefix}/integrations/api-keys"
  description = "Third-party API integration keys"
  kms_key_id  = var.kms_key_arn

  recovery_window_in_days = 7

  tags = merge(local.common_tags, {
    SecretType = "api-keys"
  })
}

resource "aws_secretsmanager_secret_version" "api_integrations" {
  secret_id = aws_secretsmanager_secret.api_integrations.id
  secret_string = jsonencode({
    openai_api_key    = ""
    anthropic_api_key = ""
    sendgrid_api_key  = ""
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# OAuth/OIDC secrets for CRM integrations
resource "aws_secretsmanager_secret" "oauth" {
  name        = "${local.prefix}/integrations/oauth"
  description = "OAuth credentials for CRM integrations"
  kms_key_id  = var.kms_key_arn

  recovery_window_in_days = 7

  tags = merge(local.common_tags, {
    SecretType = "oauth"
  })
}

resource "aws_secretsmanager_secret_version" "oauth" {
  secret_id = aws_secretsmanager_secret.oauth.id
  secret_string = jsonencode({
    salesforce = {
      client_id     = ""
      client_secret = ""
      redirect_uri  = ""
    }
    hubspot = {
      client_id     = ""
      client_secret = ""
      redirect_uri  = ""
    }
    microsoft = {
      client_id     = ""
      client_secret = ""
      tenant_id     = ""
      redirect_uri  = ""
    }
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}

# Email processing secrets
resource "aws_secretsmanager_secret" "email" {
  name        = "${local.prefix}/integrations/email"
  description = "Email service credentials"
  kms_key_id  = var.kms_key_arn

  recovery_window_in_days = 7

  tags = merge(local.common_tags, {
    SecretType = "email"
  })
}

resource "aws_secretsmanager_secret_version" "email" {
  secret_id = aws_secretsmanager_secret.email.id
  secret_string = jsonencode({
    microsoft_graph = {
      client_id     = ""
      client_secret = ""
      tenant_id     = ""
    }
    google_workspace = {
      client_id         = ""
      client_secret     = ""
      service_account   = ""
    }
  })

  lifecycle {
    ignore_changes = [secret_string]
  }
}
