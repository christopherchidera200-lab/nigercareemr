variable "name_prefix"           { type = string }
variable "environment"           { type = string }
variable "lambda_invoke_arns"    { type = map(string) }
variable "lambda_function_arns"  { type = map(string) }
variable "cognito_user_pool_arn" { type = string }
variable "cognito_user_pool_id"  { type = string }
variable "cognito_client_id"     { type = string }
