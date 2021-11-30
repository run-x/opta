output "zone_id" {
  value = aws_route53_zone.public.zone_id
}

output "name_servers" {
  value = aws_route53_zone.public.name_servers
}

output "domain" {
  value = aws_route53_zone.public.name
}

output "cert_arn" {
  value = var.delegated ? aws_acm_certificate.certificate[0].arn : (var.upload_cert ? aws_acm_certificate.imported_certificate[0].arn : var.external_cert_arn)
}