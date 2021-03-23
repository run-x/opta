resource "google_compute_firewall" "load_balancer_healthcheck" {
  name = "fw-allow-health-check-and-proxy"
  network = data.google_compute_network.vpc.name
  direction = "INGRESS"
  allow {
    protocol = "tcp"
    ports = ["9376"]
  }
  target_tags = ["opta-${var.layer_name}-nodes"]
  source_ranges = ["130.211.0.0/22", "35.191.0.0/16"]
}

resource "google_container_cluster" "primary" {
  name     = "opta-${var.layer_name}"
  location = data.google_client_config.current.region

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  network = data.google_compute_network.vpc.name
  subnetwork = data.google_compute_subnetwork.private.name
  workload_identity_config {
    identity_namespace = "${data.google_client_config.current.project}.svc.id.goog"
  }

  network_policy {
    enabled  = true
    provider = "CALICO" // CALICO is currently the only supported provider
  }

  database_encryption {
    state = "ENCRYPTED"
    key_name = data.google_kms_crypto_key.kms.self_link
  }

  master_auth {
    client_certificate_config {
      issue_client_certificate = true
    }
  }
  release_channel {
    channel = var.gke_channel
  }
  ip_allocation_policy {
    cluster_secondary_range_name = "gke-pods"
    services_secondary_range_name = "gke-services"
  }
}