resource "google_compute_network" "vpc" {
  name = "opta-${var.layer_name}"
  auto_create_subnetworks = false
  delete_default_routes_on_create = true
}


resource "google_compute_route" "default" {
  name = "opta-${var.layer_name}-${data.google_client_config.current.region}-default"
  next_hop_gateway = "default-internet-gateway"
  priority = 1000
  dest_range = "0.0.0.0/0"
  network = google_compute_network.vpc.id
}
