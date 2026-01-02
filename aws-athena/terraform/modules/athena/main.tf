# ---------------------------------------------------------------------------------------------------------------------
# ATHENA WORKGROUP AND RESOURCES
# ---------------------------------------------------------------------------------------------------------------------

# Athena Workgroup with cost controls
resource "aws_athena_workgroup" "main" {
  name        = var.workgroup_name
  description = "Analytics workgroup for ${var.project_name}"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${var.results_bucket_name}/athena-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }

    # Cost control - limit bytes scanned per query
    bytes_scanned_cutoff_per_query = var.bytes_scanned_cutoff
  }

  force_destroy = true
}

# Named queries for common analytics
resource "aws_athena_named_query" "events_by_type" {
  name        = "events_by_type"
  description = "Count events grouped by type"
  workgroup   = aws_athena_workgroup.main.name
  database    = var.database_name

  query = <<-EOT
    SELECT
      event_type,
      COUNT(*) as event_count,
      COUNT(DISTINCT user_id) as unique_users
    FROM events
    WHERE year = CAST(YEAR(CURRENT_DATE) AS VARCHAR)
      AND month = LPAD(CAST(MONTH(CURRENT_DATE) AS VARCHAR), 2, '0')
    GROUP BY event_type
    ORDER BY event_count DESC
  EOT
}

resource "aws_athena_named_query" "daily_active_users" {
  name        = "daily_active_users"
  description = "Calculate daily active users"
  workgroup   = aws_athena_workgroup.main.name
  database    = var.database_name

  query = <<-EOT
    SELECT
      year,
      month,
      day,
      COUNT(DISTINCT user_id) as dau
    FROM events
    WHERE year = CAST(YEAR(CURRENT_DATE) AS VARCHAR)
    GROUP BY year, month, day
    ORDER BY year, month, day
  EOT
}

resource "aws_athena_named_query" "user_sessions" {
  name        = "user_sessions"
  description = "Analyze user session patterns"
  workgroup   = aws_athena_workgroup.main.name
  database    = var.database_name

  query = <<-EOT
    SELECT
      user_id,
      session_id,
      MIN(timestamp) as session_start,
      MAX(timestamp) as session_end,
      COUNT(*) as event_count,
      date_diff('minute', MIN(timestamp), MAX(timestamp)) as session_duration_minutes
    FROM events
    WHERE year = CAST(YEAR(CURRENT_DATE) AS VARCHAR)
      AND session_id IS NOT NULL
    GROUP BY user_id, session_id
    ORDER BY session_start DESC
    LIMIT 100
  EOT
}

resource "aws_athena_named_query" "geo_distribution" {
  name        = "geo_distribution"
  description = "Geographic distribution of events"
  workgroup   = aws_athena_workgroup.main.name
  database    = var.database_name

  query = <<-EOT
    SELECT
      geo.country,
      geo.city,
      COUNT(*) as event_count,
      COUNT(DISTINCT user_id) as unique_users
    FROM events
    WHERE year = CAST(YEAR(CURRENT_DATE) AS VARCHAR)
      AND geo.country IS NOT NULL
    GROUP BY geo.country, geo.city
    ORDER BY event_count DESC
    LIMIT 50
  EOT
}

resource "aws_athena_named_query" "hourly_trends" {
  name        = "hourly_trends"
  description = "Hourly event trends"
  workgroup   = aws_athena_workgroup.main.name
  database    = var.database_name

  query = <<-EOT
    SELECT
      hour,
      event_type,
      COUNT(*) as event_count
    FROM events
    WHERE year = CAST(YEAR(CURRENT_DATE) AS VARCHAR)
      AND month = LPAD(CAST(MONTH(CURRENT_DATE) AS VARCHAR), 2, '0')
      AND day = LPAD(CAST(DAY(CURRENT_DATE) AS VARCHAR), 2, '0')
    GROUP BY hour, event_type
    ORDER BY hour, event_count DESC
  EOT
}

resource "aws_athena_named_query" "data_quality_check" {
  name        = "data_quality_check"
  description = "Check data quality metrics"
  workgroup   = aws_athena_workgroup.main.name
  database    = var.database_name

  query = <<-EOT
    SELECT
      year,
      month,
      day,
      COUNT(*) as total_records,
      COUNT(CASE WHEN event_id IS NULL THEN 1 END) as null_event_ids,
      COUNT(CASE WHEN user_id IS NULL THEN 1 END) as null_user_ids,
      COUNT(CASE WHEN timestamp IS NULL THEN 1 END) as null_timestamps,
      COUNT(DISTINCT event_type) as unique_event_types
    FROM events
    GROUP BY year, month, day
    ORDER BY year DESC, month DESC, day DESC
    LIMIT 30
  EOT
}
