output "load_balancer_raw_dns" {
  value = var.nginx_enabled ? data.aws_lb.ingress-nginx[0].dns_name : "n/a"
}

output "load_balancer_arn" {
  value = var.nginx_enabled ? data.aws_lb.ingress-nginx[0].arn : "n/a"
}