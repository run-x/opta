resource "google_compute_router" "router" {
  name    = "opta-${var.layer_name}"
  network = google_compute_network.vpc.id
}

resource "google_compute_address" "address" {
  count = 2
  name  = "opta-${var.layer_name}-${data.google_client_config.current.region}-${count.index}"
}

resource "google_compute_router_nat" "nat" {
  name                               = "opta-${var.layer_name}-${data.google_client_config.current.region}"
  router                             = google_compute_router.router.name
  nat_ip_allocate_option             = "MANUAL_ONLY"
  nat_ips                            = google_compute_address.address.*.self_link
  source_subnetwork_ip_ranges_to_nat = "ALL_SUBNETWORKS_ALL_IP_RANGES"

  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
}