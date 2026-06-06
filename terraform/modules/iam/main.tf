###############################################################################
# Module: IAM – NigerCare EMR
# Least-privilege execution role for all Lambda functions
###############################################################################

data "aws_iam_policy_document" "lambda_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_execution" {
  name               = "${var.name_prefix}-lambda-exec-role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role.json

  tags = {
    Name = "${var.name_prefix}-lambda-exec-role"
  }
}

###############################################################################
# Basic Lambda execution (CloudWatch Logs only)
###############################################################################
resource "aws_iam_role_policy_attachment" "lambda_basic" {
  role       = aws_iam_role.lambda_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

###############################################################################
# DynamoDB – restricted to project tables only
###############################################################################
data "aws_iam_policy_document" "lambda_dynamodb" {
  statement {
    sid    = "DynamoDBTableAccess"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:DeleteItem",
      "dynamodb:Query",
      "dynamodb:Scan",
      "dynamodb:BatchGetItem",
      "dynamodb:BatchWriteItem",
      "dynamodb:DescribeTable"
    ]
    resources = concat(
      values(var.dynamodb_table_arns),
      [for arn in values(var.dynamodb_table_arns) : "${arn}/index/*"]
    )
  }
}

resource "aws_iam_role_policy" "lambda_dynamodb" {
  name   = "${var.name_prefix}-lambda-dynamodb"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_dynamodb.json
}

###############################################################################
# S3 – scoped to medical-docs bucket only
###############################################################################
data "aws_iam_policy_document" "lambda_s3" {
  statement {
    sid    = "S3MedicalDocsAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:GetObjectAttributes"
    ]
    resources = ["${var.s3_bucket_arn}/*"]
  }

  statement {
    sid     = "S3PresignedURL"
    effect  = "Allow"
    actions = ["s3:GeneratePresignedUrl"]
    resources = ["${var.s3_bucket_arn}/*"]
  }

  statement {
    sid     = "S3ListBucket"
    effect  = "Allow"
    actions = ["s3:ListBucket"]
    resources = [var.s3_bucket_arn]
  }
}

resource "aws_iam_role_policy" "lambda_s3" {
  name   = "${var.name_prefix}-lambda-s3"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_s3.json
}

###############################################################################
# Cognito – read-only for token verification
###############################################################################
data "aws_iam_policy_document" "lambda_cognito" {
  statement {
    sid    = "CognitoReadAccess"
    effect = "Allow"
    actions = [
      "cognito-idp:AdminGetUser",
      "cognito-idp:AdminListGroupsForUser",
      "cognito-idp:ListUsers"
    ]
    resources = ["arn:aws:cognito-idp:${var.region}:${var.account_id}:userpool/*"]
  }
}

resource "aws_iam_role_policy" "lambda_cognito" {
  name   = "${var.name_prefix}-lambda-cognito"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_cognito.json
}

###############################################################################
# SNS – for notifications (Free Tier: 1M publishes/month)
###############################################################################
data "aws_iam_policy_document" "lambda_sns" {
  statement {
    sid     = "SNSPublish"
    effect  = "Allow"
    actions = ["sns:Publish"]
    resources = ["arn:aws:sns:${var.region}:${var.account_id}:*"]
  }
}

resource "aws_iam_role_policy" "lambda_sns" {
  name   = "${var.name_prefix}-lambda-sns"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_sns.json
}

###############################################################################
# CloudWatch – structured logging
###############################################################################
data "aws_iam_policy_document" "lambda_cloudwatch" {
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups"
    ]
    resources = var.log_group_arns
  }
}

resource "aws_iam_role_policy" "lambda_cloudwatch" {
  name   = "${var.name_prefix}-lambda-cloudwatch"
  role   = aws_iam_role.lambda_execution.id
  policy = data.aws_iam_policy_document.lambda_cloudwatch.json
}
