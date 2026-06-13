###############################################################################
# NigerCare EMR – Outputs (dev)
###############################################################################

output "api_gateway_url" {
  description = "Base URL of the REST API"
  value       = module.api_gateway.api_url
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.cognito.user_pool_id
}

output "cognito_user_pool_client_id" {
  description = "Cognito App Client ID (used in frontend config)"
  value       = module.cognito.user_pool_client_id
  sensitive   = true
}

output "cognito_hosted_ui_domain" {
  description = "Cognito hosted UI domain"
  value       = module.cognito.hosted_ui_domain
}

output "s3_bucket_name" {
  description = "S3 bucket name for medical document uploads"
  value       = module.s3.bucket_name
}

output "frontend_bucket_name" {
  description = "S3 bucket name for frontend static website"
  value       = module.s3.frontend_bucket_name
}

output "dynamodb_table_names" {
  description = "Map of DynamoDB table names"
  value       = module.dynamodb.table_names
}

output "cloudfront_domain" {
  description = "CloudFront domain for S3 static website (future use)"
  value       = module.s3.cloudfront_domain
}

output "lambda_function_names" {
  description = "Map of deployed Lambda function names"
  value       = module.lambda.function_names
}

output "account_id" {
  description = "AWS Account ID"
  value       = data.aws_caller_identity.current.account_id
}
