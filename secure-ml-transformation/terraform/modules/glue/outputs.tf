output "database_name" {
  description = "Glue database name"
  value       = aws_glue_catalog_database.main.name
}

output "main_etl_job_name" {
  description = "Main ETL job name"
  value       = aws_glue_job.main_etl.name
}

output "connection_name" {
  description = "Glue VPC connection name"
  value       = aws_glue_connection.vpc.name
}

output "security_configuration_name" {
  description = "Glue security configuration name"
  value       = aws_glue_security_configuration.main.name
}

output "daily_trigger_name" {
  description = "Daily trigger name"
  value       = aws_glue_trigger.daily.name
}
