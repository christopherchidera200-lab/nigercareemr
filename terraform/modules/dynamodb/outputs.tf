output "table_arns" {
  description = "Map of all DynamoDB table ARNs"
  value = {
    patients        = aws_dynamodb_table.patients.arn
    doctors         = aws_dynamodb_table.doctors.arn
    appointments    = aws_dynamodb_table.appointments.arn
    medical_records = aws_dynamodb_table.medical_records.arn
    audit_logs      = aws_dynamodb_table.audit_logs.arn
    notifications   = aws_dynamodb_table.notifications.arn
  }
}

output "table_names" {
  description = "Map of all DynamoDB table names"
  value = {
    patients        = aws_dynamodb_table.patients.name
    doctors         = aws_dynamodb_table.doctors.name
    appointments    = aws_dynamodb_table.appointments.name
    medical_records = aws_dynamodb_table.medical_records.name
    audit_logs      = aws_dynamodb_table.audit_logs.name
    notifications   = aws_dynamodb_table.notifications.name
  }
}
