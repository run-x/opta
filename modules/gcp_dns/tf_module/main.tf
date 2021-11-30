resource "google_dns_managed_zone" "public" {
  name        = "opta-${var.layer_name}"
  dns_name    = "${var.domain}."
  description = "Opta DNS for environment ${var.layer_name}"
  dnssec_config {
    kind          = "dns#managedZoneDnsSecConfig"
    non_existence = "nsec3"
    state         = "on"
    default_key_specs {
      algorithm  = "rsasha256"
      key_length = 2048
      key_type   = "keySigning"
      kind       = "dns#dnsKeySpec"
    }
    default_key_specs {
      algorithm  = "rsasha256"
      key_length = 1024
      key_type   = "zoneSigning"
      kind       = "dns#dnsKeySpec"
    }
  }
  lifecycle { ignore_changes = [dnssec_config] }
}

