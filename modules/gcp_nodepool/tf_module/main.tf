resource "random_string" "node_pool_hash" {
  length  = 4
  special = false
  lower   = true
  upper   = false
}

resource "random_string" "node_pool_id" {
  length  = 8
  special = false
  lower   = true
  upper   = false
  number  = false
}

resource "google_service_account" "gke_node" {
  account_id   = "opta-${var.layer_name}-${random_string.node_pool_hash.result}"
  display_name = "opta-${var.layer_name}-default-node-pool"
  project      = data.google_client_config.current.project
}

resource "google_project_iam_member" "gke_node_log_writer" {
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
  project = data.google_client_config.current.project
}

resource "google_project_iam_member" "gke_node_metric_writer" {
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
  project = data.google_client_config.current.project
}

resource "google_project_iam_member" "gke_node_monitoring_viewer" {
  role    = "roles/monitoring.viewer"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
  project = data.google_client_config.current.project
}

resource "google_project_iam_member" "gke_node_stackdriver_writer" {
  role    = "roles/stackdriver.resourceMetadata.writer"
  member  = "serviceAccount:${google_service_account.gke_node.email}"
  project = data.google_client_config.current.project
}

resource "google_storage_bucket_iam_member" "viewer" {
  bucket = "artifacts.${data.google_client_config.current.project}.appspot.com"
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.gke_node.email}"
  lifecycle {
    ignore_changes = [bucket]
  }
}

resource "google_container_node_pool" "node_pool" {
  name               = "opta-${var.layer_name}-${random_string.node_pool_id.id}"
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
      mode = "GKE_METADATA"
    }

    labels = {
      node_pool_name = "opta-${var.layer_name}-secondary"
    }

    dynamic "taint" {
      for_each = var.taints
      content {
        key    = taint.value["key"]
        effect = lookup(taint.value, "effect", "NO_SCHEDULE")
        value  = lookup(taint.value, "value", "opta")
      }
    }
  }
  lifecycle {
    ignore_changes = [location, initial_node_count]
  }
}