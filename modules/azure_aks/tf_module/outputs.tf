output "k8s_endpoint" {
  value = azurerm_kubernetes_cluster.main.kube_admin_config[0].host
}

output "k8s_ca_data" {
  value = azurerm_kubernetes_cluster.main.kube_admin_config[0].cluster_ca_certificate
}

output "client_cert" {
  value = azurerm_kubernetes_cluster.main.kube_admin_config[0].client_certificate
}

output "client_key" {
  value = azurerm_kubernetes_cluster.main.kube_admin_config[0].client_key
}

output "k8s_cluster_name" {
  value = azurerm_kubernetes_cluster.main.name
}