resource "azurerm_dns_zone" "opta" {
  name                = var.domain
  resource_group_name = data.azurerm_resource_group.opta.name
}

