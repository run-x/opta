resource "google_container_node_pool" "prod-main-nodes" {
  name               = var.node-pool-name
  cluster            = var.k8s-cluster-name
  initial_node_count = 1
  management {
    auto_repair  = "true"
    auto_upgrade = "true"
  }
  autoscaling {
    max_node_count = var.max-node-count
    min_node_count = var.min-node-count
  }
  node_config {
    disk_size_gb = 100
    disk_type    = "pd-standard"
    image_type   = "COS"
    machine_type = var.machine-type
    metadata = {
      "disable-legacy-endpoints" = "true"
    }
    oauth_scopes = [
      "https://www.googleapis.com/auth/devstorage.read_only",
      "https://www.googleapis.com/auth/logging.write",
      "https://www.googleapis.com/auth/monitoring",
      "https://www.googleapis.com/auth/service.management.readonly",
      "https://www.googleapis.com/auth/servicecontrol",
      "https://www.googleapis.com/auth/trace.append",
    ]
    preemptible     = false
    service_account = "default"

    shielded_instance_config {
      enable_integrity_monitoring = true
      enable_secure_boot          = false
    }
  }
}