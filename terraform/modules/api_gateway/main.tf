###############################################################################
# Module: API Gateway – NigerCare EMR
# REST API (HTTP API = cheaper but less feature-rich for RBAC)
# Free Tier: 1M API calls/month for 12 months
###############################################################################

###############################################################################
# REST API
###############################################################################
resource "aws_api_gateway_rest_api" "emr" {
  name        = "${var.name_prefix}-api"
  description = "NigerCare EMR REST API"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = {
    Name = "${var.name_prefix}-api"
  }
}

###############################################################################
# Cognito Authorizer
###############################################################################
resource "aws_api_gateway_authorizer" "cognito" {
  name                             = "${var.name_prefix}-cognito-auth"
  rest_api_id                      = aws_api_gateway_rest_api.emr.id
  type                             = "COGNITO_USER_POOLS"
  provider_arns                    = [var.cognito_user_pool_arn]
  identity_source                  = "method.request.header.Authorization"
  authorizer_result_ttl_in_seconds = 300
}

###############################################################################
# Helper – create one resource + method + integration per Lambda function
###############################################################################

# /auth  → auth lambda (PUBLIC – no authorizer)
resource "aws_api_gateway_resource" "auth" {
  rest_api_id = aws_api_gateway_rest_api.emr.id
  parent_id   = aws_api_gateway_rest_api.emr.root_resource_id
  path_part   = "auth"
}

resource "aws_api_gateway_resource" "auth_proxy" {
  rest_api_id = aws_api_gateway_rest_api.emr.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "auth_proxy" {
  rest_api_id   = aws_api_gateway_rest_api.emr.id
  resource_id   = aws_api_gateway_resource.auth_proxy.id
  http_method   = "ANY"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_proxy" {
  rest_api_id             = aws_api_gateway_rest_api.emr.id
  resource_id             = aws_api_gateway_resource.auth_proxy.id
  http_method             = aws_api_gateway_method.auth_proxy.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arns["auth"]
}

# Shared secured routes helper (patients, appointments, records, uploads, admin, notifications)
locals {
  secured_routes = {
    patients      = "patients"
    appointments  = "appointments"
    records       = "records"
    uploads       = "uploads"
    admin         = "admin"
    notifications = "notifications"
  }
}

resource "aws_api_gateway_resource" "secured" {
  for_each    = local.secured_routes
  rest_api_id = aws_api_gateway_rest_api.emr.id
  parent_id   = aws_api_gateway_rest_api.emr.root_resource_id
  path_part   = each.value
}

resource "aws_api_gateway_resource" "secured_proxy" {
  for_each    = local.secured_routes
  rest_api_id = aws_api_gateway_rest_api.emr.id
  parent_id   = aws_api_gateway_resource.secured[each.key].id
  path_part   = "{proxy+}"
}

resource "aws_api_gateway_method" "secured_proxy" {
  for_each      = local.secured_routes
  rest_api_id   = aws_api_gateway_rest_api.emr.id
  resource_id   = aws_api_gateway_resource.secured_proxy[each.key].id
  http_method   = "ANY"
  authorization = "COGNITO_USER_POOLS"
  authorizer_id = aws_api_gateway_authorizer.cognito.id

  request_parameters = {
    "method.request.header.Authorization" = true
  }
}

resource "aws_api_gateway_integration" "secured_proxy" {
  for_each                = local.secured_routes
  rest_api_id             = aws_api_gateway_rest_api.emr.id
  resource_id             = aws_api_gateway_resource.secured_proxy[each.key].id
  http_method             = aws_api_gateway_method.secured_proxy[each.key].http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arns[each.key]
}

###############################################################################
# CORS OPTIONS method for all secured resources
###############################################################################
resource "aws_api_gateway_method" "options" {
  for_each      = local.secured_routes
  rest_api_id   = aws_api_gateway_rest_api.emr.id
  resource_id   = aws_api_gateway_resource.secured_proxy[each.key].id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "options" {
  for_each    = local.secured_routes
  rest_api_id = aws_api_gateway_rest_api.emr.id
  resource_id = aws_api_gateway_resource.secured_proxy[each.key].id
  http_method = aws_api_gateway_method.options[each.key].http_method
  type        = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "options_200" {
  for_each    = local.secured_routes
  rest_api_id = aws_api_gateway_rest_api.emr.id
  resource_id = aws_api_gateway_resource.secured_proxy[each.key].id
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "options" {
  for_each    = local.secured_routes
  rest_api_id = aws_api_gateway_rest_api.emr.id
  resource_id = aws_api_gateway_resource.secured_proxy[each.key].id
  http_method = aws_api_gateway_method.options[each.key].http_method
  status_code = aws_api_gateway_method_response.options_200[each.key].status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }

  depends_on = [aws_api_gateway_integration.options]
}

###############################################################################
# Deployment + Stage
###############################################################################
resource "aws_api_gateway_deployment" "emr" {
  rest_api_id = aws_api_gateway_rest_api.emr.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_resource.auth_proxy,
      aws_api_gateway_method.auth_proxy,
      aws_api_gateway_integration.auth_proxy,
      aws_api_gateway_resource.secured_proxy,
      aws_api_gateway_method.secured_proxy,
      aws_api_gateway_integration.secured_proxy,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }

  depends_on = [
    aws_api_gateway_integration.auth_proxy,
    aws_api_gateway_integration.secured_proxy,
    aws_api_gateway_integration_response.options,
  ]
}

resource "aws_api_gateway_stage" "dev" {
  deployment_id = aws_api_gateway_deployment.emr.id
  rest_api_id   = aws_api_gateway_rest_api.emr.id
  stage_name    = var.environment

  # Access logging (free log group, minimal cost)
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access.arn
  }

  xray_tracing_enabled = false # Disable X-Ray to avoid charges

  tags = {
    Name = "${var.name_prefix}-api-stage"
  }
}

resource "aws_cloudwatch_log_group" "api_access" {
  name              = "/aws/apigateway/${var.name_prefix}-access"
  retention_in_days = 7
}

###############################################################################
# API Gateway account-level CloudWatch role (required once per account)
###############################################################################
resource "aws_api_gateway_account" "emr" {
  cloudwatch_role_arn = aws_iam_role.api_gateway_cloudwatch.arn
}

data "aws_iam_policy_document" "api_gateway_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["apigateway.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "api_gateway_cloudwatch" {
  name               = "${var.name_prefix}-apigw-cw-role"
  assume_role_policy = data.aws_iam_policy_document.api_gateway_assume.json
}

resource "aws_iam_role_policy_attachment" "api_gateway_cloudwatch" {
  role       = aws_iam_role.api_gateway_cloudwatch.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonAPIGatewayPushToCloudWatchLogs"
}
