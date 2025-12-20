# API Gateway for ML Inference

resource "aws_apigatewayv2_api" "this" {
  name          = "${var.project_prefix}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = ["*"]
    allow_methods = ["POST", "GET", "OPTIONS"]
    allow_headers = ["Content-Type", "Authorization"]
    max_age       = 300
  }

  tags = var.tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      routeKey       = "$context.routeKey"
      status         = "$context.status"
      responseLength = "$context.responseLength"
      integrationError = "$context.integrationErrorMessage"
    })
  }
}

resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/aws/apigateway/${var.project_prefix}-api"
  retention_in_days = 14
  tags              = var.tags
}

# Inference endpoint
resource "aws_apigatewayv2_integration" "inference" {
  api_id             = aws_apigatewayv2_api.this.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.inference_lambda_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "inference" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /inference"
  target    = "integrations/${aws_apigatewayv2_integration.inference.id}"
}

resource "aws_lambda_permission" "inference" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.inference_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# Generation endpoint
resource "aws_apigatewayv2_integration" "generate" {
  api_id             = aws_apigatewayv2_api.this.id
  integration_type   = "AWS_PROXY"
  integration_uri    = var.bedrock_lambda_arn
  integration_method = "POST"
}

resource "aws_apigatewayv2_route" "generate" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /generate"
  target    = "integrations/${aws_apigatewayv2_integration.generate.id}"
}

resource "aws_lambda_permission" "generate" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.bedrock_lambda_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}
