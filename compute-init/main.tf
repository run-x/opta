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
  workload_identity_config {
    identity_namespace = "${data.google_project.caller.project_id}.svc.id.goog"
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