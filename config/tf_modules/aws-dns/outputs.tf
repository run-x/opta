output "zone_id" {
  value = var.is_private ? aws_route53_zone.private[0].zone_id : aws_route53_zone.public[0].zone_id
}

output "name_servers" {
  value = var.is_private ? aws_route53_zone.private[0].name_servers : aws_route53_zone.public[0].name_servers
}