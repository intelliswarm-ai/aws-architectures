output "database_name" {
  description = "Name of the Glue database"
  value       = aws_glue_catalog_database.main.name
}

output "database_arn" {
  description = "ARN of the Glue database"
  value       = aws_glue_catalog_database.main.arn
}

output "etl_job_name" {
  description = "Name of the ETL job"
  value       = aws_glue_job.json_to_parquet.name
}

output "etl_job_arn" {
  description = "ARN of the ETL job"
  value       = aws_glue_job.json_to_parquet.arn
}

output "crawler_name" {
  description = "Name of the crawler"
  value       = aws_glue_crawler.parquet.name
}

output "raw_table_name" {
  description = "Name of the raw events table"
  value       = aws_glue_catalog_table.raw_events.name
}

output "events_table_name" {
  description = "Name of the processed events table"
  value       = aws_glue_catalog_table.events.name
}
