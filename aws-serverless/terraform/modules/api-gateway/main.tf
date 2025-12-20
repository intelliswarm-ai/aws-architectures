# =============================================================================
# API Gateway Module - REST API with Enterprise Security
# =============================================================================

locals {
  api_name = "${var.project_name}-${var.environment}-${var.api_name}"

  common_tags = merge(var.tags, {
    Module      = "api-gateway"
    Environment = var.environment
  })
}

# -----------------------------------------------------------------------------
# REST API
# -----------------------------------------------------------------------------
resource "aws_api_gateway_rest_api" "this" {
  name        = local.api_name
  description = var.api_description

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Request Validator
# -----------------------------------------------------------------------------
resource "aws_api_gateway_request_validator" "all" {
  count = var.enable_request_validation ? 1 : 0

  name                        = "validate-all"
  rest_api_id                 = aws_api_gateway_rest_api.this.id
  validate_request_body       = true
  validate_request_parameters = true
}

# -----------------------------------------------------------------------------
# Cognito Authorizer
# -----------------------------------------------------------------------------
resource "aws_api_gateway_authorizer" "cognito" {
  count = var.enable_cognito_authorizer && var.cognito_user_pool_arn != null ? 1 : 0

  name            = "${local.api_name}-cognito-authorizer"
  rest_api_id     = aws_api_gateway_rest_api.this.id
  type            = "COGNITO_USER_POOLS"
  provider_arns   = [var.cognito_user_pool_arn]
  identity_source = "method.request.header.Authorization"
}

# -----------------------------------------------------------------------------
# Lambda Authorizer
# -----------------------------------------------------------------------------
resource "aws_api_gateway_authorizer" "lambda" {
  count = var.enable_lambda_authorizer && var.lambda_authorizer_arn != null ? 1 : 0

  name                             = "${local.api_name}-lambda-authorizer"
  rest_api_id                      = aws_api_gateway_rest_api.this.id
  type                             = "TOKEN"
  authorizer_uri                   = var.lambda_authorizer_invoke_arn
  authorizer_credentials           = aws_iam_role.api_gateway[0].arn
  authorizer_result_ttl_in_seconds = var.authorizer_result_ttl
  identity_source                  = "method.request.header.Authorization"
}

# IAM Role for API Gateway to invoke Lambda authorizer
resource "aws_iam_role" "api_gateway" {
  count = var.enable_lambda_authorizer ? 1 : 0

  name = "${local.api_name}-api-gateway-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "apigateway.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy" "api_gateway_invoke" {
  count = var.enable_lambda_authorizer ? 1 : 0

  name = "${local.api_name}-invoke-policy"
  role = aws_iam_role.api_gateway[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = "lambda:InvokeFunction"
        Resource = var.lambda_authorizer_arn
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# API Resources and Methods
# -----------------------------------------------------------------------------
# Proxy resource for all paths
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  parent_id   = aws_api_gateway_rest_api.this.root_resource_id
  path_part   = "{proxy+}"
}

# ANY method on proxy resource
resource "aws_api_gateway_method" "proxy" {
  rest_api_id   = aws_api_gateway_rest_api.this.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = var.enable_cognito_authorizer ? "COGNITO_USER_POOLS" : (var.enable_lambda_authorizer ? "CUSTOM" : "NONE")
  authorizer_id = var.enable_cognito_authorizer ? aws_api_gateway_authorizer.cognito[0].id : (var.enable_lambda_authorizer ? aws_api_gateway_authorizer.lambda[0].id : null)
  api_key_required = var.enable_api_key

  request_validator_id = var.enable_request_validation ? aws_api_gateway_request_validator.all[0].id : null
}

# Lambda integration for proxy
resource "aws_api_gateway_integration" "proxy" {
  rest_api_id             = aws_api_gateway_rest_api.this.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_function_invoke_arn
}

# Root method
resource "aws_api_gateway_method" "root" {
  rest_api_id   = aws_api_gateway_rest_api.this.id
  resource_id   = aws_api_gateway_rest_api.this.root_resource_id
  http_method   = "ANY"
  authorization = var.enable_cognito_authorizer ? "COGNITO_USER_POOLS" : (var.enable_lambda_authorizer ? "CUSTOM" : "NONE")
  authorizer_id = var.enable_cognito_authorizer ? aws_api_gateway_authorizer.cognito[0].id : (var.enable_lambda_authorizer ? aws_api_gateway_authorizer.lambda[0].id : null)
  api_key_required = var.enable_api_key
}

# Lambda integration for root
resource "aws_api_gateway_integration" "root" {
  rest_api_id             = aws_api_gateway_rest_api.this.id
  resource_id             = aws_api_gateway_rest_api.this.root_resource_id
  http_method             = aws_api_gateway_method.root.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_function_invoke_arn
}

# -----------------------------------------------------------------------------
# CORS Configuration
# -----------------------------------------------------------------------------
resource "aws_api_gateway_method" "options" {
  count = var.enable_cors ? 1 : 0

  rest_api_id   = aws_api_gateway_rest_api.this.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  count = var.enable_cors ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.options[0].http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = jsonencode({ statusCode = 200 })
  }
}

resource "aws_api_gateway_method_response" "options" {
  count = var.enable_cors ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.options[0].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }

  response_models = {
    "application/json" = "Empty"
  }
}

resource "aws_api_gateway_integration_response" "options" {
  count = var.enable_cors ? 1 : 0

  rest_api_id = aws_api_gateway_rest_api.this.id
  resource_id = aws_api_gateway_resource.proxy.id
  http_method = aws_api_gateway_method.options[0].http_method
  status_code = aws_api_gateway_method_response.options[0].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'${join(",", var.cors_allow_headers)}'"
    "method.response.header.Access-Control-Allow-Methods" = "'${join(",", var.cors_allow_methods)}'"
    "method.response.header.Access-Control-Allow-Origin"  = "'${join(",", var.cors_allow_origins)}'"
  }
}

# -----------------------------------------------------------------------------
# Lambda Permission
# -----------------------------------------------------------------------------
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_arn
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.this.execution_arn}/*"
}

# -----------------------------------------------------------------------------
# Deployment and Stage
# -----------------------------------------------------------------------------
resource "aws_api_gateway_deployment" "this" {
  rest_api_id = aws_api_gateway_rest_api.this.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.proxy.id,
      aws_api_gateway_method.proxy.id,
      aws_api_gateway_integration.proxy.id,
      aws_api_gateway_method.root.id,
      aws_api_gateway_integration.root.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.proxy,
    aws_api_gateway_integration.root
  ]
}

# CloudWatch Log Group for access logs
resource "aws_cloudwatch_log_group" "api_gateway" {
  count = var.enable_access_logging ? 1 : 0

  name              = "/aws/api-gateway/${local.api_name}"
  retention_in_days = var.log_retention_days

  tags = local.common_tags
}

resource "aws_api_gateway_stage" "this" {
  deployment_id = aws_api_gateway_deployment.this.id
  rest_api_id   = aws_api_gateway_rest_api.this.id
  stage_name    = var.stage_name

  variables = var.stage_variables

  xray_tracing_enabled = true

  dynamic "access_log_settings" {
    for_each = var.enable_access_logging ? [1] : []
    content {
      destination_arn = aws_cloudwatch_log_group.api_gateway[0].arn
      format = jsonencode({
        requestId         = "$context.requestId"
        ip                = "$context.identity.sourceIp"
        caller            = "$context.identity.caller"
        user              = "$context.identity.user"
        requestTime       = "$context.requestTime"
        httpMethod        = "$context.httpMethod"
        resourcePath      = "$context.resourcePath"
        status            = "$context.status"
        protocol          = "$context.protocol"
        responseLength    = "$context.responseLength"
        integrationStatus = "$context.integrationStatus"
        integrationError  = "$context.integration.error"
      })
    }
  }

  tags = local.common_tags
}

# Method Settings for throttling
resource "aws_api_gateway_method_settings" "all" {
  rest_api_id = aws_api_gateway_rest_api.this.id
  stage_name  = aws_api_gateway_stage.this.stage_name
  method_path = "*/*"

  settings {
    throttling_burst_limit = var.throttling_burst_limit
    throttling_rate_limit  = var.throttling_rate_limit
    metrics_enabled        = true
    logging_level          = "INFO"
    data_trace_enabled     = var.environment != "prod"  # Disable in prod for security
  }
}

# -----------------------------------------------------------------------------
# Usage Plan and API Key
# -----------------------------------------------------------------------------
resource "aws_api_gateway_usage_plan" "this" {
  count = var.enable_api_key ? 1 : 0

  name        = "${local.api_name}-usage-plan"
  description = "Usage plan for ${local.api_name}"

  api_stages {
    api_id = aws_api_gateway_rest_api.this.id
    stage  = aws_api_gateway_stage.this.stage_name
  }

  quota_settings {
    limit  = var.usage_plan_quota_limit
    period = var.usage_plan_quota_period
  }

  throttle_settings {
    burst_limit = var.throttling_burst_limit
    rate_limit  = var.throttling_rate_limit
  }

  tags = local.common_tags
}

resource "aws_api_gateway_api_key" "this" {
  count = var.enable_api_key ? 1 : 0

  name    = "${local.api_name}-api-key"
  enabled = true

  tags = local.common_tags
}

resource "aws_api_gateway_usage_plan_key" "this" {
  count = var.enable_api_key ? 1 : 0

  key_id        = aws_api_gateway_api_key.this[0].id
  key_type      = "API_KEY"
  usage_plan_id = aws_api_gateway_usage_plan.this[0].id
}

# -----------------------------------------------------------------------------
# WAF Association
# -----------------------------------------------------------------------------
resource "aws_wafv2_web_acl_association" "api_gateway" {
  count = var.waf_acl_arn != null ? 1 : 0

  resource_arn = aws_api_gateway_stage.this.arn
  web_acl_arn  = var.waf_acl_arn
}
