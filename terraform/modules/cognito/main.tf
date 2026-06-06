###############################################################################
# Module: Cognito – NigerCare EMR
# Free Tier: 50,000 MAUs/month
# Pools: Doctors, Patients, Admins (single pool, group-based RBAC)
###############################################################################

resource "aws_cognito_user_pool" "emr" {
  name = "${var.name_prefix}-user-pool"

  # Username / login options
  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  # Password policy – healthcare-grade
  password_policy {
    minimum_length                   = 12
    require_uppercase                = true
    require_lowercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 3
  }

  # MFA: OPTIONAL – user can enroll TOTP
  mfa_configuration = "OPTIONAL"
  software_token_mfa_configuration {
    enabled = true
  }

  # Account recovery via email only (no SMS cost)
  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  # Email configuration – use Cognito default for Free Tier
  # (100 free emails/day; switch to SES for production volume)
  email_configuration {
    email_sending_account = "COGNITO_DEFAULT"
  }

  # User attributes (standard + custom)
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
    string_attribute_constraints {
      min_length = 5
      max_length = 254
    }
  }

  schema {
    name                = "name"
    attribute_data_type = "String"
    required            = true
    mutable             = true
    string_attribute_constraints {
      min_length = 1
      max_length = 100
    }
  }

  schema {
    name                = "role"
    attribute_data_type = "String"
    required            = false
    mutable             = true
    string_attribute_constraints {
      min_length = 1
      max_length = 20
    }
  }

  # Verification message
  verification_message_template {
    default_email_option = "CONFIRM_WITH_CODE"
    email_subject        = "NigerCare EMR – Verify your email"
    email_message        = "Your NigerCare EMR verification code is {####}. This code expires in 24 hours."
  }

  # Token validity
  user_pool_add_ons {
    advanced_security_mode = "AUDIT"  # Free; ENFORCED costs extra
  }

  tags = {
    Name = "${var.name_prefix}-user-pool"
  }
}

###############################################################################
# User Pool Domain (Cognito hosted UI – no extra charge)
###############################################################################
resource "aws_cognito_user_pool_domain" "emr" {
  domain       = "${var.name_prefix}-auth"
  user_pool_id = aws_cognito_user_pool.emr.id
}

###############################################################################
# App Client – React SPA (no client secret for public client)
###############################################################################
resource "aws_cognito_user_pool_client" "spa" {
  name         = "${var.name_prefix}-spa-client"
  user_pool_id = aws_cognito_user_pool.emr.id

  generate_secret = false # Public client (React SPA)

  # Auth flows
  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_PASSWORD_AUTH"
  ]

  # Token validity
  access_token_validity  = 1   # 1 hour
  id_token_validity      = 1   # 1 hour
  refresh_token_validity = 30  # 30 days

  token_validity_units {
    access_token  = "hours"
    id_token      = "hours"
    refresh_token = "days"
  }

  # OAuth
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers         = ["COGNITO"]

  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  # Prevent user existence errors (security)
  prevent_user_existence_errors = "ENABLED"

  # Read/write attributes
  read_attributes  = ["email", "name", "custom:role"]
  write_attributes = ["email", "name", "custom:role"]
}

###############################################################################
# RBAC Groups
###############################################################################
resource "aws_cognito_user_group" "admins" {
  name         = "Admins"
  user_pool_id = aws_cognito_user_pool.emr.id
  description  = "Hospital administrators with full access"
  precedence   = 1
}

resource "aws_cognito_user_group" "doctors" {
  name         = "Doctors"
  user_pool_id = aws_cognito_user_pool.emr.id
  description  = "Licensed medical practitioners"
  precedence   = 2
}

resource "aws_cognito_user_group" "patients" {
  name         = "Patients"
  user_pool_id = aws_cognito_user_pool.emr.id
  description  = "Registered patients"
  precedence   = 3
}
