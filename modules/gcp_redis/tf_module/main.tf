locals {
  identifier = var.identifier == null ? "opta-${var.layer_name}-${var.module_name}" : var.identifier
}

# TODO: TLS transit encryption
resource "google_redis_instance" "main" {
  memory_size_gb     = var.memory_size_gb
  name               = local.identifier
  display_name       = local.identifier
  tier               = var.high_availability ? "STANDARD_HA" : "BASIC"
  authorized_network = data.google_compute_network.vpc.id
  connect_mode       = "PRIVATE_SERVICE_ACCESS"
  redis_version      = var.redis_version
  auth_enabled       = true
}
