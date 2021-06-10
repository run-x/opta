output "zone_id" {
  value = google_dns_managed_zone.public.id
}

output "zone_name" {
  value = google_dns_managed_zone.public.name
}

output "name_servers" {
  value = google_dns_managed_zone.public.name_servers
}

output "domain" {
  // This comes out with a trailing . which causes problems downstream
  value = trim(google_dns_managed_zone.public.dns_name, ".")
}

output "delegated" {
  value = var.delegated
}

output "cert_self_link" {
  value = var.delegated ? google_compute_managed_ssl_certificate.certificate[0].self_link : null
}
