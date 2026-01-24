################################################################################
# AWS Glue Resources for ETL Processing
################################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

################################################################################
# Glue Database
################################################################################

resource "aws_glue_catalog_database" "main" {
  name        = replace("${var.name_prefix}_db", "-", "_")
  description = "Database for ${var.project_name} ML transformation pipeline"
}

################################################################################
# Glue Connection (VPC)
################################################################################

resource "aws_glue_connection" "vpc" {
  name            = "${var.name_prefix}-vpc-connection"
  connection_type = "NETWORK"

  physical_connection_requirements {
    availability_zone      = data.aws_availability_zones.available.names[0]
    security_group_id_list = [var.glue_security_group_id]
    subnet_id              = var.private_subnet_ids[0]
  }

  tags = {
    Name = "${var.name_prefix}-vpc-connection"
  }
}

data "aws_availability_zones" "available" {
  state = "available"
}

################################################################################
# Glue Security Configuration
################################################################################

resource "aws_glue_security_configuration" "main" {
  name = "${var.name_prefix}-security-config"

  encryption_configuration {
    cloudwatch_encryption {
      cloudwatch_encryption_mode = "SSE-KMS"
      kms_key_arn                = var.kms_key_arn
    }

    job_bookmarks_encryption {
      job_bookmarks_encryption_mode = "CSE-KMS"
      kms_key_arn                   = var.kms_key_arn
    }

    s3_encryption {
      s3_encryption_mode = "SSE-KMS"
      kms_key_arn        = var.kms_key_arn
    }
  }
}

################################################################################
# Main ETL Job
################################################################################

resource "aws_glue_job" "main_etl" {
  name        = "${var.name_prefix}-main-etl"
  description = "Main ETL job for ML data transformation"
  role_arn    = var.glue_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.scripts_bucket}/glue/jobs/main_etl.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--job-bookmark-option"              = "job-bookmark-enable"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-spark-ui"                  = "true"
    "--spark-event-logs-path"            = "s3://${var.processed_data_bucket}/spark-logs/"
    "--TempDir"                          = "s3://${var.processed_data_bucket}/temp/"
    "--source_bucket"                    = var.raw_data_bucket
    "--target_bucket"                    = var.processed_data_bucket
    "--environment"                      = var.environment
    "--extra-py-files"                   = "s3://${var.scripts_bucket}/glue/jobs/pii_tokenization.py,s3://${var.scripts_bucket}/glue/jobs/amount_binning.py,s3://${var.scripts_bucket}/glue/jobs/merchant_encoding.py,s3://${var.scripts_bucket}/glue/jobs/anomaly_detection.py"
  }

  connections = [aws_glue_connection.vpc.name]

  security_configuration = aws_glue_security_configuration.main.name

  execution_property {
    max_concurrent_runs = 1
  }

  glue_version      = "4.0"
  worker_type       = var.glue_worker_type
  number_of_workers = var.glue_number_of_workers
  timeout           = var.glue_job_timeout

  tags = {
    Name = "${var.name_prefix}-main-etl"
  }
}

################################################################################
# Glue Trigger (Scheduled)
################################################################################

resource "aws_glue_trigger" "daily" {
  name     = "${var.name_prefix}-daily-trigger"
  type     = "SCHEDULED"
  schedule = "cron(0 2 * * ? *)" # 2 AM daily
  enabled  = false               # Set to true in production

  actions {
    job_name = aws_glue_job.main_etl.name
    arguments = {
      "--source_path" = "s3://${var.raw_data_bucket}/transactions/"
    }
  }

  tags = {
    Name = "${var.name_prefix}-daily-trigger"
  }
}

################################################################################
# Raw Data Table
################################################################################

resource "aws_glue_catalog_table" "raw_transactions" {
  name          = "raw_transactions"
  database_name = aws_glue_catalog_database.main.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    classification  = "parquet"
    compressionType = "snappy"
  }

  storage_descriptor {
    location      = "s3://${var.raw_data_bucket}/transactions/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "transaction_id"
      type = "string"
    }
    columns {
      name = "customer_id"
      type = "string"
    }
    columns {
      name = "account_number"
      type = "string"
    }
    columns {
      name = "card_number"
      type = "string"
    }
    columns {
      name = "email"
      type = "string"
    }
    columns {
      name = "phone"
      type = "string"
    }
    columns {
      name = "transaction_amount"
      type = "decimal(18,2)"
    }
    columns {
      name = "currency"
      type = "string"
    }
    columns {
      name = "merchant_category_code"
      type = "string"
    }
    columns {
      name = "merchant_name"
      type = "string"
    }
    columns {
      name = "transaction_timestamp"
      type = "timestamp"
    }
    columns {
      name = "location_country"
      type = "string"
    }
    columns {
      name = "location_city"
      type = "string"
    }
  }
}

################################################################################
# Processed Data Table
################################################################################

resource "aws_glue_catalog_table" "processed_transactions" {
  name          = "processed_transactions"
  database_name = aws_glue_catalog_database.main.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    classification  = "parquet"
    compressionType = "snappy"
  }

  partition_keys {
    name = "processing_date"
    type = "date"
  }

  storage_descriptor {
    location      = "s3://${var.processed_data_bucket}/ml-ready/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name    = "transaction_id"
      type    = "string"
      comment = ""
    }
    columns {
      name    = "customer_id"
      type    = "string"
      comment = "Tokenized"
    }
    columns {
      name    = "transaction_amount"
      type    = "decimal(18,2)"
      comment = ""
    }
    columns {
      name = "transaction_amount_bin"
      type = "string"
    }
    columns {
      name = "transaction_amount_bin_encoded"
      type = "int"
    }
    columns {
      name = "merchant_category"
      type = "string"
    }
    columns {
      name = "merchant_risk_score"
      type = "float"
    }
    columns {
      name = "is_anomaly"
      type = "boolean"
    }
    columns {
      name = "anomaly_score"
      type = "float"
    }
  }
}
