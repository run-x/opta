output "zone_id" {
  value = google_dns_managed_zone.public.id
}

output "name_servers" {
  value = google_dns_managed_zone.public.name_servers
}

output "domain" {
  value = google_dns_managed_zone.public.dns_name
}

output "delegated" {
  value = var.delegated ? true : false
}