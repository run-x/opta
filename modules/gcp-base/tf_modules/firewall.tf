resource "google_compute_firewall" "firewall" {
  name      = "opta-${var.layer_name}-${data.google_client_config.current.region}-private"
  network   = google_compute_network.vpc.id
  direction = "INGRESS"
  allow {
    protocol = "tcp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "udp"
    ports    = ["0-65535"]
  }
  allow {
    protocol = "icmp"
  }
  source_ranges = [var.private_ipv4_cidr_block]
}

resource "google_compute_firewall" "k8s_extra_rules" {
  name      = "opta-${var.layer_name}-k8s-cntrol-plane"
  network   = google_compute_network.vpc.id
  direction = "INGRESS"
  allow {
    protocol = "tcp"
    ports    = ["8443"]
  }
  source_ranges = [var.k8s_master_ipv4_cidr_block]
  target_tags   = ["opta-${var.layer_name}-nodes"]
}