output "endpoint_name" {
  value = "${var.project_prefix}-endpoint"
}

output "endpoint_config_name" {
  value = aws_sagemaker_endpoint_configuration.this.name
}
