output "sns_alert_topic_arn" {
  value = aws_sns_topic.alerts.arn
}

output "log_group_arns" {
  value = ["arn:aws:logs:*:${var.account_id}:log-group:/aws/lambda/${var.name_prefix}-*"]
}
