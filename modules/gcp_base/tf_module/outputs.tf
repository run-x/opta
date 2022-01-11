output "kms_account_key_id" {
  value = google_kms_key_ring.keyring.id
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

output "k8s_master_ipv4_cidr_block" {
  value = var.k8s_master_ipv4_cidr_block
}

output "public_nat_ips" {
  value = google_compute_address.address
}
