###############################################################################
# NigerCare EMR – Terraform Variable Values (dev)
# IMPORTANT: Do NOT commit real secrets. Use GitHub Secrets / AWS Secrets Mgr.
###############################################################################

aws_region   = "us-east-1"
environment  = "dev"
project_name = "nigercareemr"

ses_from_email = "christopherchidera200@gmail.com"

cognito_callback_urls = [
  "https://nigercaremedicals.com/callback",
  "http://localhost:3000/callback"
]

cognito_logout_urls = [
  "https://nigercaremedicals.com/logout",
  "http://localhost:3000/logout"
]

alert_email          = "christopherchidera200@gmail.com"
monthly_budget_limit = "2"
