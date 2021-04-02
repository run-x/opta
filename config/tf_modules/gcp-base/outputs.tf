output "kms_account_key_id" {
  value = google_kms_key_ring.keyring.id
}

output "kms_account_key_self_link" {
  value = google_kms_key_ring.keyring.self_link
}

output "vpc_id" {
  value = google_compute_network.vpc.id
}

output "vpc_self_link" {
  value = google_compute_network.vpc.id
}

output "private_subnet_id" {
  value = google_compute_subnetwork.project_subnet.self_link
}

output "private_subnet_self_link" {
  value = google_compute_subnetwork.project_subnet.self_link
}
