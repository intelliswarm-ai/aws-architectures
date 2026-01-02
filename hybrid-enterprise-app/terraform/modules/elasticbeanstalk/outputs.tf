output "application_name" {
  description = "Elastic Beanstalk application name"
  value       = aws_elastic_beanstalk_application.main.name
}

output "environment_name" {
  description = "Elastic Beanstalk environment name"
  value       = aws_elastic_beanstalk_environment.main.name
}

output "application_url" {
  description = "Application URL"
  value       = "http://${aws_elastic_beanstalk_environment.main.cname}"
}

output "environment_id" {
  description = "Environment ID"
  value       = aws_elastic_beanstalk_environment.main.id
}
