resource "random_string" "node_group_hash" {
  length  = 4
  special = false
  lower   = true
  upper   = false
}

// https://cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster#use_least_privilege_sa
resource "google_service_account" "gke_node" {
  account_id   = "opta-${var.layer_name}-${random_string.node_group_hash.result}"
  display_name = "opta-${var.layer_name}-default-node-pool"
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