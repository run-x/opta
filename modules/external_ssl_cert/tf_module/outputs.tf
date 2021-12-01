output "private_key" {
  value     = var.private_key
  sensitive = true
}

output "certificate_body" {
  value     = var.certificate_body
  sensitive = true
}

output "certificate_chain" {
  value     = var.certificate_chain
  sensitive = true
}

output "domain" {
  value = var.domain
}
