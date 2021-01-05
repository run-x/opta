output "gcp-network" {
  value = google_compute_network.private-network.id
}

output "k8s-cluster" {
  value = google_container_cluster.prod-main
}
