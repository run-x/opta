resource "random_string" "node_pool_hash" {
  length  = 4
  special = false
  lower   = true
  upper   = false
}

resource "google_service_account" "gke_node" {
  account_id   = "opta-${var.layer_name}-${random_string.node_pool_hash.result}"
  display_name = "opta-${var.layer_name}-default-node-pool"
}

resource "google_container_node_pool" "node_pool" {
  name               = "opta-${var.layer_name}-secondary"
  cluster            = data.google_container_cluster.main.name
  location           = data.google_client_config.current.region
  initial_node_count = var.min_nodes

  autoscaling {
    max_node_count = var.max_nodes
    min_node_count = var.min_nodes
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  node_config {
    preemptible  = var.preemptible
    machine_type = var.node_instance_type
    disk_size_gb = var.node_disk_size
    tags         = ["opta-${var.layer_name}-nodes"]

    service_account = google_service_account.gke_node.email
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform",
    ]
    metadata = {
      disable-legacy-endpoints = true
    }

    workload_metadata_config {
      node_metadata = "GKE_METADATA_SERVER"
    }

    labels = {
      node_pool_name = "opta-${var.layer_name}-default"
    }
  }
  lifecycle {
    ignore_changes = [location, initial_node_count]
  }
}