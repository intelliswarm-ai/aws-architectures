# SageMaker Endpoint (Optional)
# Note: This creates an empty endpoint configuration.
# The actual model deployment is handled by the training pipeline.

resource "aws_sagemaker_endpoint_configuration" "this" {
  name = "${var.project_prefix}-endpoint-config"

  production_variants {
    variant_name           = "primary"
    model_name             = "${var.project_prefix}-model"
    initial_instance_count = var.instance_count
    instance_type          = var.instance_type
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}
