resource "google_compute_managed_ssl_certificate" "certificate" {
  count = var.delegated ? 1 : 0
  name = "opta-${var.layer_name}"

  managed {
    domains = [var.domain]
  }
}