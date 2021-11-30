resource "random_id" "cert_suffix" {
  byte_length = 8
  keepers = {
    domains = join(",", concat([var.domain], local.full_subdomains))
  }
}

resource "google_compute_managed_ssl_certificate" "certificate" {
  count = var.delegated ? 1 : 0
  name  = "opta-${var.layer_name}-${random_id.cert_suffix.hex}"

  managed {
    domains = concat([var.domain], local.full_subdomains)
  }
  lifecycle {
    create_before_destroy = true
  }
}