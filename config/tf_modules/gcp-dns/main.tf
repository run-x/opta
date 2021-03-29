resource "google_dns_managed_zone" "public" {
  name        = "opta-${var.layer_name}"
  dns_name    = "${var.domain}."
  description = "Opta DNS for environment ${var.layer_name}"
}

