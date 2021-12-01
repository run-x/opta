output "k8s_endpoint" {
  value = google_container_cluster.primary.endpoint
}

output "k8s_ca_data" {
  value = google_container_cluster.primary.master_auth[0].cluster_ca_certificate
}

output "k8s_cluster_name" {
  value = google_container_cluster.primary.name
}
