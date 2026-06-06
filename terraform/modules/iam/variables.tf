variable "name_prefix"        { type = string }
variable "account_id"         { type = string }
variable "region"             { type = string }
variable "environment"        { type = string }
variable "project_name"       { type = string }
variable "dynamodb_table_arns" { type = map(string) }
variable "s3_bucket_arn"      { type = string }
variable "log_group_arns"     { type = list(string) }
