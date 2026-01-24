output "endpoint_name" {
  description = "SageMaker endpoint name"
  value       = aws_sagemaker_endpoint.main.name
}

output "endpoint_arn" {
  description = "SageMaker endpoint ARN"
  value       = aws_sagemaker_endpoint.main.arn
}

output "endpoint_config_name" {
  description = "SageMaker endpoint configuration name"
  value       = aws_sagemaker_endpoint_configuration.main.name
}

output "model_name" {
  description = "SageMaker model name"
  value       = aws_sagemaker_model.production.name
}
