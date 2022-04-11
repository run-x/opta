output "load_balancer_raw_dns" {
  value = data.aws_lb.ingress-nginx.dns_name
}

output "load_balancer_arn" {
  value = data.aws_lb.ingress-nginx.arn
}