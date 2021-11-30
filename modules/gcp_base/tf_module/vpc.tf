resource "google_compute_network" "vpc" {
  name                            = "opta-${var.layer_name}"
  auto_create_subnetworks         = false
  delete_default_routes_on_create = true
}


resource "google_compute_route" "default" {
  name             = "opta-${var.layer_name}-${data.google_client_config.current.region}-default"
  next_hop_gateway = "default-internet-gateway"
  priority         = 1000
  dest_range       = "0.0.0.0/0"
  network          = google_compute_network.vpc.id
}

resource "google_compute_global_address" "private_ip_alloc" {
  name          = "opta-${var.layer_name}-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 22
  network       = google_compute_network.vpc.id
}

resource "google_service_networking_connection" "private_services" {
  network                 = google_compute_network.vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}
