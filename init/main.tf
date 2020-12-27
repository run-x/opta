// TODO: These need to be enabled in a separate step
resource "google_project_service" "service-networking" {
  service = "servicenetworking.googleapis.com"
}

resource "google_project_service" "compute" {
  service = "compute.googleapis.com"
}

resource "google_project_service" "container" {
  service = "container.googleapis.com"
}

resource "google_compute_network" "private-network" {
  name    = var.name
}

resource "google_compute_global_address" "vpc-peering-range" {
  name          = var.name
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.private-network.id
}

resource "google_service_networking_connection" "vpc-connection" {
  network                 = google_compute_network.private-network.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.vpc-peering-range.name]
}

resource "google_container_cluster" "prod-main" {
  name                     = var.name
  remove_default_node_pool = true
  initial_node_count       = 1
  cluster_autoscaling {
    enabled = false
  }
  master_auth {
    username = ""
    password = ""

    client_certificate_config {
      issue_client_certificate = false
    }
  }

  # This is needed to enable vpc-native routing - which enables connecting to
  # our postgres dbs with ip addresses
  ip_allocation_policy {
    cluster_ipv4_cidr_block  = ""
    services_ipv4_cidr_block = ""
  }
  network = google_compute_network.private-network.id
}

resource "google_container_node_pool" "prod-main-nodes" {
  name               = var.name
  cluster            = google_container_cluster.prod-main.name
  initial_node_count = 1
  management {
    auto_repair  = "true"
    auto_upgrade = "true"
  }
  node_config {
    disk_size_gb = 100
    disk_type    = "pd-standard"
    image_type   = "COS"
    machine_type = "e2-standard-4"
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
