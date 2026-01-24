# SageMaker Module - Endpoint configuration with traffic splitting

data "aws_region" "current" {}

# SageMaker Model
resource "aws_sagemaker_model" "production" {
  name               = "${var.project_prefix}-production"
  execution_role_arn = var.execution_role_arn

  primary_container {
    image          = "763104351884.dkr.ecr.${data.aws_region.current.name}.amazonaws.com/xgboost:1.7-1"
    model_data_url = var.initial_model_data != "" ? var.initial_model_data : null
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

# Endpoint Configuration with production variant
resource "aws_sagemaker_endpoint_configuration" "main" {
  name = "${var.project_prefix}-config"

  production_variants {
    variant_name           = "production"
    model_name             = aws_sagemaker_model.production.name
    instance_type          = var.instance_type
    initial_instance_count = var.initial_instance_count
    initial_variant_weight = 1.0

    model_data_download_timeout_in_seconds            = 3600
    container_startup_health_check_timeout_in_seconds = 600
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

# SageMaker Endpoint
resource "aws_sagemaker_endpoint" "main" {
  name                 = "${var.project_prefix}-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.main.name

  tags = var.tags
}

# Auto-scaling target
resource "aws_appautoscaling_target" "endpoint" {
  count              = var.enable_auto_scaling ? 1 : 0
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "endpoint/${aws_sagemaker_endpoint.main.name}/variant/production"
  scalable_dimension = "sagemaker:variant:DesiredInstanceCount"
  service_namespace  = "sagemaker"
}

# Auto-scaling policy
resource "aws_appautoscaling_policy" "endpoint" {
  count              = var.enable_auto_scaling ? 1 : 0
  name               = "${var.project_prefix}-scaling-policy"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.endpoint[0].resource_id
  scalable_dimension = aws_appautoscaling_target.endpoint[0].scalable_dimension
  service_namespace  = aws_appautoscaling_target.endpoint[0].service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "SageMakerVariantInvocationsPerInstance"
    }
    target_value       = var.target_invocations
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}
