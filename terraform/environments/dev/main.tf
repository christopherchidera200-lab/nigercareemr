###############################################################################
# NigerCare Medical Centre EMR – Dev Environment
# Region: us-east-1  |  Target Cost: $0.00/month (Free Tier maximized)
###############################################################################

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  # NOTE: For first-time deploy, comment out the backend block and run
  # terraform init locally, then uncomment after state bucket exists.
  # Using local state initially keeps cost at $0 (no S3 state bucket needed).
  backend "s3" {
    bucket         = "nigercareemr-tfstate-873871686800"
    key            = "dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "nigercareemr-tfstate-lock"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "NigerCareEMR"
      Environment = var.environment
      ManagedBy   = "Terraform"
      CostCenter  = "Healthcare-Dev"
    }
  }
}

###############################################################################
# Data Sources
###############################################################################

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

###############################################################################
# Random suffix for globally unique resource names
###############################################################################

resource "random_id" "suffix" {
  byte_length = 4
}

###############################################################################
# Local values
###############################################################################

locals {
  account_id    = data.aws_caller_identity.current.account_id
  region        = data.aws_region.current.name
  name_prefix   = "${var.project_name}-${var.environment}"
  resource_suffix = random_id.suffix.hex

  # Lambda source paths
  lambda_source_dir = "${path.root}/../../../backend/lambdas"
}

###############################################################################
# Module: IAM Roles & Policies
###############################################################################

module "iam" {
  source = "../../modules/iam"

  name_prefix  = local.name_prefix
  account_id   = local.account_id
  region       = local.region
  environment  = var.environment
  project_name = var.project_name

  dynamodb_table_arns = module.dynamodb.table_arns
  s3_bucket_arn       = module.s3.bucket_arn
  log_group_arns      = ["arn:aws:logs:${var.aws_region}:*:log-group:/aws/lambda/${local.name_prefix}-*:*"]
}

###############################################################################
# Module: DynamoDB Tables
###############################################################################

module "dynamodb" {
  source = "../../modules/dynamodb"

  name_prefix = local.name_prefix
  environment = var.environment
}

###############################################################################
# Module: S3 Buckets
###############################################################################

module "s3" {
  source = "../../modules/s3"

  name_prefix     = local.name_prefix
  resource_suffix = local.resource_suffix
  environment     = var.environment
  account_id      = local.account_id
}

###############################################################################
# Module: Cognito User Pools
###############################################################################

module "cognito" {
  source = "../../modules/cognito"

  name_prefix     = local.name_prefix
  environment     = var.environment
  ses_email       = var.ses_from_email
  callback_urls   = var.cognito_callback_urls
  logout_urls     = var.cognito_logout_urls
}

###############################################################################
# Module: Lambda Functions
###############################################################################

module "lambda" {
  source = "../../modules/lambda"

  name_prefix         = local.name_prefix
  environment         = var.environment
  lambda_role_arn     = module.iam.lambda_execution_role_arn
  lambda_source_dir   = local.lambda_source_dir

  dynamodb_table_names = module.dynamodb.table_names
  s3_bucket_name       = module.s3.bucket_name
  cognito_user_pool_id = module.cognito.user_pool_id
  cognito_client_id    = module.cognito.user_pool_client_id
  sns_topic_arn        = module.cloudwatch.sns_alert_topic_arn

  depends_on = [module.iam, module.dynamodb, module.s3, module.cognito]
}

###############################################################################
# Module: API Gateway
###############################################################################

module "api_gateway" {
  source = "../../modules/api_gateway"

  name_prefix          = local.name_prefix
  environment          = var.environment
  lambda_invoke_arns   = module.lambda.invoke_arns
  lambda_function_arns = module.lambda.function_arns
  cognito_user_pool_arn = module.cognito.user_pool_arn
  cognito_user_pool_id  = module.cognito.user_pool_id
  cognito_client_id     = module.cognito.user_pool_client_id

  depends_on = [module.lambda, module.cognito]
}

###############################################################################
# Module: CloudWatch, Budgets & Monitoring
###############################################################################

module "cloudwatch" {
  source = "../../modules/cloudwatch"

  name_prefix     = local.name_prefix
  environment     = var.environment
  account_id      = local.account_id
  alert_email     = var.alert_email
  budget_limit    = var.monthly_budget_limit
  lambda_function_names = values(module.lambda.function_names)
}

###############################################################################
# Module: AWS Budgets (Zero-Cost Guard)
###############################################################################

module "budgets" {
  source = "../../modules/budgets"

  name_prefix   = local.name_prefix
  alert_email   = var.alert_email
  budget_limit  = var.monthly_budget_limit
}
