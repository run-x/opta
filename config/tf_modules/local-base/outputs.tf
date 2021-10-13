output "k8s_cluster_name" {
  value = var.local_k8s_cluster_name
}

output "public_nat_ips" {
  value = tolist([local.ifconfig_co_json.ip])
}