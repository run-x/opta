resource "google_compute_firewall" "firewall" {
  name = "opta-${var.layer_name}-${data.google_client_config.current.region}-private"
  network = google_compute_network.vpc.id
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