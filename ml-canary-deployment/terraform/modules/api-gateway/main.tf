# API Gateway Module - REST API for inference and management

resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.project_prefix}-api"
  description = "ML Canary Deployment API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# /inference endpoint
resource "aws_api_gateway_resource" "inference" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "inference"
}

resource "aws_api_gateway_method" "inference_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.inference.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "inference" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.inference.id
  http_method             = aws_api_gateway_method.inference_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.inference_lambda_arn}/invocations"
}

resource "aws_lambda_permission" "inference" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.inference_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# /deployments endpoint
resource "aws_api_gateway_resource" "deployments" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "deployments"
}

resource "aws_api_gateway_method" "deployments_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.deployments.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "deployments" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.deployments.id
  http_method             = aws_api_gateway_method.deployments_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.deployment_lambda_arn}/invocations"
}

resource "aws_lambda_permission" "deployments" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.deployment_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# /traffic endpoint
resource "aws_api_gateway_resource" "traffic" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "traffic"
}

resource "aws_api_gateway_method" "traffic_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.traffic.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "traffic" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.traffic.id
  http_method             = aws_api_gateway_method.traffic_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.traffic_shift_lambda_arn}/invocations"
}

resource "aws_lambda_permission" "traffic" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.traffic_shift_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# /rollback endpoint
resource "aws_api_gateway_resource" "rollback" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "rollback"
}

resource "aws_api_gateway_method" "rollback_post" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.rollback.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "rollback" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.rollback.id
  http_method             = aws_api_gateway_method.rollback_post.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:lambda:path/2015-03-31/functions/${var.rollback_lambda_arn}/invocations"
}

resource "aws_lambda_permission" "rollback" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.rollback_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

# Deployment
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  depends_on = [
    aws_api_gateway_integration.inference,
    aws_api_gateway_integration.deployments,
    aws_api_gateway_integration.traffic,
    aws_api_gateway_integration.rollback,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "main" {
  deployment_id = aws_api_gateway_deployment.main.id
  rest_api_id   = aws_api_gateway_rest_api.main.id
  stage_name    = var.stage_name

  tags = var.tags
}

data "aws_region" "current" {}
