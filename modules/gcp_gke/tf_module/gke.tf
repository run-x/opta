# PSP is deprecated in Kubernetes, no point adding it.
# google gke legacy metadata endpoints  are disabled in the node group (see default_node_group.tf)
#tfsec:ignore:google-gke-enforce-pod-security-policy
#tfsec:ignore:google-gke-enable-master-networks
#tfsec:ignore:google-gke-metadata-endpoints-disabled
resource "google_container_cluster" "primary" {
  name           = var.cluster_name
  location       = data.google_client_config.current.region
  node_locations = var.node_zone_names

  # We can't create a cluster with no node pool defined, but we want to only use
  # separately managed node pools. So we create the smallest possible default
  # node pool and immediately delete it.
  remove_default_node_pool = true
  initial_node_count       = 1

  network               = var.vpc_self_link
  subnetwork            = var.private_subnet_self_link
  enable_shielded_nodes = true
  workload_identity_config {
    workload_pool = "${data.google_client_config.current.project}.svc.id.goog"
  }

  private_cluster_config {
    enable_private_nodes    = true
    enable_private_endpoint = false
    master_ipv4_cidr_block  = var.k8s_master_ipv4_cidr_block
  }

  network_policy {
    enabled  = true
    provider = "CALICO" // CALICO is currently the only supported provider
  }

  database_encryption {
    state    = "ENCRYPTED"
    key_name = data.google_kms_crypto_key.kms.id
  }

  master_auth {
    client_certificate_config {
      # tfsec recomments using oauth or SA, we ignore this since opta currently
      # uses client certificate for auth. 
      # https://aquasecurity.github.io/tfsec/v1.8.0/checks/google/gke/no-legacy-authentication/
      #tfsec:ignore:google-gke-no-legacy-authentication
      issue_client_certificate = true
    }
  }
  release_channel {
    channel = var.gke_channel
  }
  ip_allocation_policy {
    cluster_secondary_range_name  = "gke-pods"
    services_secondary_range_name = "gke-services"
  }
  lifecycle {
    ignore_changes = [location, private_cluster_config, enable_shielded_nodes]
  }
}
