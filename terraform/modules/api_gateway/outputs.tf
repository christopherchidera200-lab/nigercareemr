output "api_url" {
  value = "https://${aws_api_gateway_rest_api.emr.id}.execute-api.${data.aws_region.current.name}.amazonaws.com/${var.environment}"
}

output "api_id" {
  value = aws_api_gateway_rest_api.emr.id
}

data "aws_region" "current" {}
