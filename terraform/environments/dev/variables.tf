###############################################################################
# NigerCare EMR – Variable Definitions (dev)
###############################################################################

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev | staging | prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Short project identifier used in resource names"
  type        = string
  default     = "nigercareemr"
}

variable "ses_from_email" {
  description = "Verified SES sender email for Cognito notifications"
  type        = string
  default     = "noreply@nigercaremedicals.com"
}

variable "cognito_callback_urls" {
  description = "Allowed OAuth callback URLs for Cognito app client"
  type        = list(string)
  default     = [
    "https://nigercaremedicals.com/callback",
    "http://localhost:3000/callback"
  ]
}

variable "cognito_logout_urls" {
  description = "Allowed logout URLs for Cognito app client"
  type        = list(string)
  default     = [
    "https://nigercaremedicals.com/logout",
    "http://localhost:3000/logout"
  ]
}

variable "alert_email" {
  description = "Email address for CloudWatch alarms and budget notifications"
  type        = string
  default     = "admin@nigercaremedicals.com"
}

variable "monthly_budget_limit" {
  description = "Monthly spend threshold in USD before alarm fires"
  type        = string
  default     = "5"
}
