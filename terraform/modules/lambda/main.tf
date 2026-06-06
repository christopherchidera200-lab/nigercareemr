###############################################################################
# Module: Lambda – NigerCare EMR
# Free Tier: 1M requests/month + 400,000 GB-seconds compute
# All functions: 128 MB, Python 3.12, 30s timeout
###############################################################################

locals {
  runtime     = "python3.12"
  timeout     = 30
  memory_size = 128

  functions = {
    auth          = "auth"
    patients      = "patients"
    appointments  = "appointments"
    records       = "records"
    uploads       = "uploads"
    admin         = "admin"
    notifications = "notifications"
  }
}

###############################################################################
# Archive each Lambda directory into a ZIP
###############################################################################
data "archive_file" "lambda_zips" {
  for_each    = local.functions
  type        = "zip"
  source_dir  = "${var.lambda_source_dir}/${each.value}"
  output_path = "${path.module}/builds/${each.key}.zip"
}

###############################################################################
# CloudWatch Log Groups (created before functions to set retention)
###############################################################################
resource "aws_cloudwatch_log_group" "lambda_logs" {
  for_each          = local.functions
  name              = "/aws/lambda/${var.name_prefix}-${each.key}"
  retention_in_days = 7  # Keep low to avoid log storage charges

  tags = {
    Function = each.key
  }
}

###############################################################################
# Lambda Functions
###############################################################################
resource "aws_lambda_function" "functions" {
  for_each = local.functions

  function_name = "${var.name_prefix}-${each.key}"
  description   = "NigerCare EMR – ${each.key} handler"
  role          = var.lambda_role_arn
  handler       = "handler.lambda_handler"
  runtime       = local.runtime
  timeout       = local.timeout
  memory_size   = local.memory_size

  filename         = data.archive_file.lambda_zips[each.key].output_path
  source_code_hash = data.archive_file.lambda_zips[each.key].output_base64sha256

  environment {
    variables = {
      ENVIRONMENT              = var.environment
      PATIENTS_TABLE           = var.dynamodb_table_names["patients"]
      DOCTORS_TABLE            = var.dynamodb_table_names["doctors"]
      APPOINTMENTS_TABLE       = var.dynamodb_table_names["appointments"]
      MEDICAL_RECORDS_TABLE    = var.dynamodb_table_names["medical_records"]
      AUDIT_LOGS_TABLE         = var.dynamodb_table_names["audit_logs"]
      NOTIFICATIONS_TABLE      = var.dynamodb_table_names["notifications"]
      S3_BUCKET                = var.s3_bucket_name
      COGNITO_USER_POOL_ID     = var.cognito_user_pool_id
      COGNITO_CLIENT_ID        = var.cognito_client_id
      SNS_TOPIC_ARN            = var.sns_topic_arn
      AWS_ACCOUNT_ID           = data.aws_caller_identity.current.account_id
      REGION                   = data.aws_region.current.name
    }
  }

  depends_on = [
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = {
    Function = each.key
  }
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

###############################################################################
# Lambda permissions – allow API Gateway to invoke each function
###############################################################################
resource "aws_lambda_permission" "api_gateway" {
  for_each = local.functions

  statement_id  = "AllowAPIGatewayInvoke-${each.key}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.functions[each.key].function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "arn:aws:execute-api:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*/*/*"
}
