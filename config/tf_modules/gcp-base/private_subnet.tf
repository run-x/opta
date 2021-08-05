resource "google_compute_subnetwork" "project_subnet" {
  name                     = "opta-${var.layer_name}-${data.google_client_config.current.region}-private"
  ip_cidr_range            = var.private_ipv4_cidr_block
  private_ip_google_access = true
  network                  = google_compute_network.vpc.id
  secondary_ip_range {
    ip_cidr_range = var.cluster_ipv4_cidr_block
    range_name    = "gke-pods"
  }
  secondary_ip_range {
    ip_cidr_range = var.services_ipv4_cidr_block
    range_name    = "gke-services"
  }
  log_config {
    aggregation_interval = "INTERVAL_5_SEC"
    flow_sampling        = "0.5"
    metadata             = "INCLUDE_ALL_METADATA"
  }
}
