output "cloudfront_domain" {
  value = var.bucket_name != "" ? aws_cloudfront_distribution.s3_distribution[0].domain_name : aws_cloudfront_distribution.lb_distribution[0].domain_name
}