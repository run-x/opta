output "cloudfront_domain" {
  value = aws_cloudfront_distribution.distribution.domain_name
}