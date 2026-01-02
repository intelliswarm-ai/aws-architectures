# ---------------------------------------------------------------------------------------------------------------------
# GLUE DATABASE AND ETL RESOURCES
# ---------------------------------------------------------------------------------------------------------------------

# Glue Database (Data Catalog)
resource "aws_glue_catalog_database" "main" {
  name        = var.database_name
  description = "Data lake analytics database for ${var.project_name}"
}

# Raw events table (JSON)
resource "aws_glue_catalog_table" "raw_events" {
  name          = "raw_events"
  database_name = aws_glue_catalog_database.main.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    classification = "json"
    "projection.enabled" = "true"
    "projection.year.type" = "integer"
    "projection.year.range" = "2020,2030"
    "projection.month.type" = "integer"
    "projection.month.range" = "1,12"
    "projection.month.digits" = "2"
    "projection.day.type" = "integer"
    "projection.day.range" = "1,31"
    "projection.day.digits" = "2"
    "projection.hour.type" = "integer"
    "projection.hour.range" = "0,23"
    "projection.hour.digits" = "2"
    "storage.location.template" = "s3://${var.raw_bucket_name}/raw/year=$${year}/month=$${month}/day=$${day}/hour=$${hour}"
  }

  storage_descriptor {
    location      = "s3://${var.raw_bucket_name}/raw/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
    }

    columns {
      name = "event_id"
      type = "string"
    }
    columns {
      name = "timestamp"
      type = "timestamp"
    }
    columns {
      name = "event_type"
      type = "string"
    }
    columns {
      name = "user_id"
      type = "string"
    }
    columns {
      name = "session_id"
      type = "string"
    }
    columns {
      name = "properties"
      type = "map<string,string>"
    }
    columns {
      name = "geo"
      type = "struct<country:string,city:string,lat:double,lon:double>"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
  partition_keys {
    name = "hour"
    type = "string"
  }
}

# Processed events table (Parquet)
resource "aws_glue_catalog_table" "events" {
  name          = "events"
  database_name = aws_glue_catalog_database.main.name

  table_type = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
    "parquet.compression" = "SNAPPY"
    "projection.enabled" = "true"
    "projection.year.type" = "integer"
    "projection.year.range" = "2020,2030"
    "projection.month.type" = "integer"
    "projection.month.range" = "1,12"
    "projection.month.digits" = "2"
    "projection.day.type" = "integer"
    "projection.day.range" = "1,31"
    "projection.day.digits" = "2"
    "projection.hour.type" = "integer"
    "projection.hour.range" = "0,23"
    "projection.hour.digits" = "2"
    "storage.location.template" = "s3://${var.processed_bucket_name}/processed/year=$${year}/month=$${month}/day=$${day}/hour=$${hour}"
  }

  storage_descriptor {
    location      = "s3://${var.processed_bucket_name}/processed/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
      parameters = {
        "serialization.format" = "1"
      }
    }

    columns {
      name = "event_id"
      type = "string"
    }
    columns {
      name = "timestamp"
      type = "timestamp"
    }
    columns {
      name = "event_type"
      type = "string"
    }
    columns {
      name = "user_id"
      type = "string"
    }
    columns {
      name = "session_id"
      type = "string"
    }
    columns {
      name = "properties"
      type = "map<string,string>"
    }
    columns {
      name = "geo"
      type = "struct<country:string,city:string,lat:double,lon:double>"
    }
  }

  partition_keys {
    name = "year"
    type = "string"
  }
  partition_keys {
    name = "month"
    type = "string"
  }
  partition_keys {
    name = "day"
    type = "string"
  }
  partition_keys {
    name = "hour"
    type = "string"
  }
}

# Upload ETL script to S3
resource "aws_s3_object" "etl_script" {
  bucket = var.etl_script_bucket
  key    = "glue-scripts/etl_job.py"
  source = "${path.module}/../../../glue/etl_job.py"
  etag   = filemd5("${path.module}/../../../glue/etl_job.py")
}

# Glue ETL Job
resource "aws_glue_job" "json_to_parquet" {
  name     = var.etl_job_name
  role_arn = var.glue_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${var.etl_script_bucket}/glue-scripts/etl_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"                     = "python"
    "--enable-metrics"                   = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--enable-glue-datacatalog"          = "true"
    "--source_path"                      = "s3://${var.raw_bucket_name}/raw/"
    "--target_path"                      = "s3://${var.processed_bucket_name}/processed/"
    "--database"                         = var.database_name
    "--table_name"                       = "events"
    "--partition_year"                   = "2024"
    "--partition_month"                  = "01"
    "--partition_day"                    = "01"
    "--partition_hour"                   = "00"
  }

  glue_version      = "4.0"
  worker_type       = var.worker_type
  number_of_workers = var.number_of_workers
  timeout           = 60

  execution_property {
    max_concurrent_runs = 2
  }
}

# Glue Crawler for processed data
resource "aws_glue_crawler" "parquet" {
  name          = var.crawler_name
  database_name = aws_glue_catalog_database.main.name
  role          = var.glue_role_arn

  s3_target {
    path = "s3://${var.processed_bucket_name}/processed/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  configuration = jsonencode({
    Version = 1.0
    Grouping = {
      TableGroupingPolicy = "CombineCompatibleSchemas"
    }
    CrawlerOutput = {
      Partitions = {
        AddOrUpdateBehavior = "InheritFromTable"
      }
    }
  })
}
