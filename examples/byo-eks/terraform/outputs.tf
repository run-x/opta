
output "account_id" {
  value = data.aws_caller_identity.current.account_id
}

output "load_balancer_raw_dns" {
  value = data.aws_lb.ingress-nginx.dns_name
}
