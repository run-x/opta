output "vpc_id" {
  value = azurerm_virtual_network.opta.id
}

output "vpc_name" {
  value = azurerm_virtual_network.opta.name
}

output "private_subnet_id" {
  value = azurerm_subnet.opta.id
}

output "private_subnet_name" {
  value = azurerm_subnet.opta.name
}

output "acr_id" {
  value = azurerm_container_registry.acr.id
}

output "acr_name" {
  value = azurerm_container_registry.acr.name
}

output "acr_login_url" {
  value = azurerm_container_registry.acr.login_server
}

output "public_nat_ips" {
  value = azurerm_public_ip.opta.ip_address
}
