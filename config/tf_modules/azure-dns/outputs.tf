output "zone_id" {
  value = azurerm_dns_zone.opta.id
}

output "name_servers" {
  value = azurerm_dns_zone.opta.name_servers
}

output "domain" {
  value = azurerm_dns_zone.opta.name
}

output "delegated" {
  value = var.delegated
}
