output "bucket_name" {
  value = aws_s3_bucket.medical_docs.bucket
}

output "bucket_arn" {
  value = aws_s3_bucket.medical_docs.arn
}

output "frontend_bucket_name" {
  value = aws_s3_bucket.frontend.bucket
}

output "cloudfront_domain" {
  value = aws_cloudfront_distribution.frontend.domain_name
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.frontend.id
}
