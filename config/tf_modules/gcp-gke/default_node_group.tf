resource "google_container_node_pool" "default" {
  name       = "opta-${var.layer_name}-default"
  cluster    = google_container_cluster.primary.name
  location = data.google_client_config.current.region
  initial_node_count = var.min_nodes

  autoscaling {
    max_node_count = var.max_nodes
    min_node_count = var.min_nodes
  }

  management {
    auto_repair = true
    auto_upgrade = true
  }

  node_config {
    preemptible  = false
    machine_type = var.node_instance_type
    disk_size_gb = var.node_disk_size
    tags = ["opta-${var.layer_name}-nodes"]

    service_account = google_service_account.gke_node.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]

    workload_metadata_config {
      node_metadata = "SECURE"
    }
  }
}