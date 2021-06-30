resource "azurerm_virtual_network" "opta" {
  name                = "opta-${var.env_name}"
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name
  address_space       = [var.private_ipv4_cidr_block]
}

resource "azurerm_subnet" "opta" {
  name                                           = "opta-${var.env_name}-subnet"
  resource_group_name                            = data.azurerm_resource_group.opta.name
  virtual_network_name                           = azurerm_virtual_network.opta.name
  address_prefixes                               = [var.subnet_ipv4_cidr_block]
  enforce_private_link_endpoint_network_policies = true
}