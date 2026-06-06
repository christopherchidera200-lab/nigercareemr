###############################################################################
# Module: DynamoDB – NigerCare EMR
# All tables use PAY_PER_REQUEST (on-demand) = Free Tier friendly
# Free Tier: 25 GB storage, 200M requests/month
###############################################################################

###############################################################################
# PATIENTS table
# PK: patient_id  |  SK: "PROFILE"
# GSI1: email-index  → lookup by email
# GSI2: phone-index  → lookup by phone
###############################################################################
resource "aws_dynamodb_table" "patients" {
  name         = "${var.name_prefix}-patients"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "patient_id"
  range_key    = "record_type"

  attribute {
    name = "patient_id"
    type = "S"
  }
  attribute {
    name = "record_type"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }
  attribute {
    name = "phone"
    type = "S"
  }

  global_secondary_index {
    name               = "email-index"
    hash_key           = "email"
    projection_type    = "ALL"
  }

  global_secondary_index {
    name               = "phone-index"
    hash_key           = "phone"
    projection_type    = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-patients"
    PHI  = "true"
  }
}

###############################################################################
# DOCTORS table
# PK: doctor_id  |  SK: "PROFILE"
# GSI1: specialty-index
# GSI2: email-index
###############################################################################
resource "aws_dynamodb_table" "doctors" {
  name         = "${var.name_prefix}-doctors"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "doctor_id"
  range_key    = "record_type"

  attribute {
    name = "doctor_id"
    type = "S"
  }
  attribute {
    name = "record_type"
    type = "S"
  }
  attribute {
    name = "specialty"
    type = "S"
  }
  attribute {
    name = "email"
    type = "S"
  }

  global_secondary_index {
    name               = "specialty-index"
    hash_key           = "specialty"
    range_key          = "doctor_id"
    projection_type    = "ALL"
  }

  global_secondary_index {
    name               = "email-index"
    hash_key           = "email"
    projection_type    = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-doctors"
  }
}

###############################################################################
# APPOINTMENTS table
# PK: appointment_id  |  SK: appointment_date
# GSI1: patient-date-index  → patient's appointments sorted by date
# GSI2: doctor-date-index   → doctor's schedule sorted by date
# GSI3: status-index        → filter by status (PENDING|CONFIRMED|CANCELLED)
###############################################################################
resource "aws_dynamodb_table" "appointments" {
  name         = "${var.name_prefix}-appointments"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "appointment_id"
  range_key    = "appointment_date"

  attribute {
    name = "appointment_id"
    type = "S"
  }
  attribute {
    name = "appointment_date"
    type = "S"
  }
  attribute {
    name = "patient_id"
    type = "S"
  }
  attribute {
    name = "doctor_id"
    type = "S"
  }
  attribute {
    name = "status"
    type = "S"
  }

  global_secondary_index {
    name               = "patient-date-index"
    hash_key           = "patient_id"
    range_key          = "appointment_date"
    projection_type    = "ALL"
  }

  global_secondary_index {
    name               = "doctor-date-index"
    hash_key           = "doctor_id"
    range_key          = "appointment_date"
    projection_type    = "ALL"
  }

  global_secondary_index {
    name               = "status-index"
    hash_key           = "status"
    range_key          = "appointment_date"
    projection_type    = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-appointments"
  }
}

###############################################################################
# MEDICAL_RECORDS table
# PK: patient_id  |  SK: record_id (timestamp-prefixed for sort)
# GSI1: doctor-records-index → doctor's authored records
# GSI2: record-type-index    → filter by DIAGNOSIS|LAB|PRESCRIPTION|NOTE
###############################################################################
resource "aws_dynamodb_table" "medical_records" {
  name         = "${var.name_prefix}-medical-records"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "patient_id"
  range_key    = "record_id"

  attribute {
    name = "patient_id"
    type = "S"
  }
  attribute {
    name = "record_id"
    type = "S"
  }
  attribute {
    name = "doctor_id"
    type = "S"
  }
  attribute {
    name = "record_type"
    type = "S"
  }

  global_secondary_index {
    name               = "doctor-records-index"
    hash_key           = "doctor_id"
    range_key          = "record_id"
    projection_type    = "ALL"
  }

  global_secondary_index {
    name               = "record-type-index"
    hash_key           = "record_type"
    range_key          = "record_id"
    projection_type    = "ALL"
  }

  point_in_time_recovery {
    enabled = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-medical-records"
    PHI  = "true"
  }
}

###############################################################################
# AUDIT_LOGS table
# PK: log_id  |  SK: timestamp
# GSI1: user-activity-index  → all actions by a user
# TTL on "expires_at" attribute (90-day auto-expiry to control storage cost)
###############################################################################
resource "aws_dynamodb_table" "audit_logs" {
  name         = "${var.name_prefix}-audit-logs"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "log_id"
  range_key    = "timestamp"

  attribute {
    name = "log_id"
    type = "S"
  }
  attribute {
    name = "timestamp"
    type = "S"
  }
  attribute {
    name = "user_id"
    type = "S"
  }

  global_secondary_index {
    name               = "user-activity-index"
    hash_key           = "user_id"
    range_key          = "timestamp"
    projection_type    = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-audit-logs"
  }
}

###############################################################################
# NOTIFICATIONS table
# PK: notification_id  |  SK: created_at
# GSI1: recipient-index → all notifications for a user
# TTL: 30-day auto-expiry
###############################################################################
resource "aws_dynamodb_table" "notifications" {
  name         = "${var.name_prefix}-notifications"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "notification_id"
  range_key    = "created_at"

  attribute {
    name = "notification_id"
    type = "S"
  }
  attribute {
    name = "created_at"
    type = "S"
  }
  attribute {
    name = "recipient_id"
    type = "S"
  }

  global_secondary_index {
    name               = "recipient-index"
    hash_key           = "recipient_id"
    range_key          = "created_at"
    projection_type    = "ALL"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  server_side_encryption {
    enabled = true
  }

  tags = {
    Name = "${var.name_prefix}-notifications"
  }
}
