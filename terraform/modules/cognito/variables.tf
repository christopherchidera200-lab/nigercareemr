variable "name_prefix"   { type = string }
variable "environment"   { type = string }
variable "ses_email"     { type = string }
variable "callback_urls" { type = list(string) }
variable "logout_urls"   { type = list(string) }
