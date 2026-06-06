output "function_names" {
  value = { for k, fn in aws_lambda_function.functions : k => fn.function_name }
}

output "function_arns" {
  value = { for k, fn in aws_lambda_function.functions : k => fn.arn }
}

output "invoke_arns" {
  value = { for k, fn in aws_lambda_function.functions : k => fn.invoke_arn }
}

output "log_group_arns" {
  value = [for lg in aws_cloudwatch_log_group.lambda_logs : lg.arn]
}
