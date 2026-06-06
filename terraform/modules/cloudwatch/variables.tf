variable "name_prefix"           { type = string }
variable "environment"           { type = string }
variable "account_id"            { type = string }
variable "alert_email"           { type = string }
variable "budget_limit"          { type = string }
variable "lambda_function_names" { type = list(string) }
