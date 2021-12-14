output "cloudfront_domain" {
  value = var.s3_load_balancer_enabled == true ? aws_cloudfront_distribution.s3_distribution[0].domain_name : (var.eks_load_balancer_enabled == true ? aws_cloudfront_distribution.lb_distribution[0].domain_name : "")
}