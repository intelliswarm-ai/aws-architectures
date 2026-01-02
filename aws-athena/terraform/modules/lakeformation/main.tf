# ---------------------------------------------------------------------------------------------------------------------
# LAKE FORMATION DATA GOVERNANCE
# Provides fine-grained access control for the data lake
# ---------------------------------------------------------------------------------------------------------------------

data "aws_caller_identity" "current" {}

# Configure Lake Formation settings
resource "aws_lakeformation_data_lake_settings" "main" {
  admins = var.admin_arns

  # Disable IAM-only permissions to enforce Lake Formation
  create_database_default_permissions {
    principal   = "IAM_ALLOWED_PRINCIPALS"
    permissions = []
  }

  create_table_default_permissions {
    principal   = "IAM_ALLOWED_PRINCIPALS"
    permissions = []
  }
}

# Register raw data S3 location
resource "aws_lakeformation_resource" "raw" {
  arn      = var.raw_bucket_arn
  role_arn = var.lakeformation_role_arn

  # Use service-linked role if no specific role provided
  use_service_linked_role = var.lakeformation_role_arn == null
}

# Register processed data S3 location
resource "aws_lakeformation_resource" "processed" {
  arn      = var.processed_bucket_arn
  role_arn = var.lakeformation_role_arn

  use_service_linked_role = var.lakeformation_role_arn == null
}

# Grant database permissions to Glue role
resource "aws_lakeformation_permissions" "glue_database" {
  principal   = var.glue_role_arn
  permissions = ["CREATE_TABLE", "DESCRIBE", "ALTER", "DROP"]

  database {
    name = var.database_name
  }
}

# Grant table permissions to Glue role
resource "aws_lakeformation_permissions" "glue_tables" {
  principal   = var.glue_role_arn
  permissions = ["SELECT", "INSERT", "DELETE", "DESCRIBE", "ALTER"]

  table {
    database_name = var.database_name
    wildcard      = true
  }
}

# Grant data location access to Glue role (raw bucket)
resource "aws_lakeformation_permissions" "glue_raw_location" {
  principal   = var.glue_role_arn
  permissions = ["DATA_LOCATION_ACCESS"]

  data_location {
    arn = var.raw_bucket_arn
  }

  depends_on = [aws_lakeformation_resource.raw]
}

# Grant data location access to Glue role (processed bucket)
resource "aws_lakeformation_permissions" "glue_processed_location" {
  principal   = var.glue_role_arn
  permissions = ["DATA_LOCATION_ACCESS"]

  data_location {
    arn = var.processed_bucket_arn
  }

  depends_on = [aws_lakeformation_resource.processed]
}

# Grant database permissions to Lambda role
resource "aws_lakeformation_permissions" "lambda_database" {
  principal   = var.lambda_role_arn
  permissions = ["DESCRIBE"]

  database {
    name = var.database_name
  }
}

# Grant table SELECT permissions to Lambda role
resource "aws_lakeformation_permissions" "lambda_tables" {
  principal   = var.lambda_role_arn
  permissions = ["SELECT", "DESCRIBE"]

  table {
    database_name = var.database_name
    wildcard      = true
  }
}

# LF-Tag for data classification (optional)
resource "aws_lakeformation_lf_tag" "sensitivity" {
  key    = "DataSensitivity"
  values = ["public", "internal", "confidential", "restricted"]
}

resource "aws_lakeformation_lf_tag" "domain" {
  key    = "DataDomain"
  values = ["analytics", "events", "users", "transactions"]
}
