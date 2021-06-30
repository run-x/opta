resource "azurerm_public_ip" "opta" {
  name                = "opta-${var.env_name}-nat-public-ip"
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_public_ip_prefix" "opta" {
  name                = "opta-${var.env_name}-nat-public-ip-prefix"
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name
  prefix_length       = 30
}

resource "azurerm_nat_gateway" "opta" {
  name                    = "opta-${var.env_name}-nat-gateway"
  location                = data.azurerm_resource_group.opta.location
  resource_group_name     = data.azurerm_resource_group.opta.name
  sku_name                = "Standard"
  idle_timeout_in_minutes = 10
}

resource "azurerm_nat_gateway_public_ip_prefix_association" "opta" {
  nat_gateway_id      = azurerm_nat_gateway.opta.id
  public_ip_prefix_id = azurerm_public_ip_prefix.opta.id
}

resource "azurerm_nat_gateway_public_ip_association" "opta" {
  nat_gateway_id       = azurerm_nat_gateway.opta.id
  public_ip_address_id = azurerm_public_ip.opta.id
}

resource "azurerm_subnet_nat_gateway_association" "opta" {
  subnet_id      = azurerm_subnet.opta.id
  nat_gateway_id = azurerm_nat_gateway.opta.id
}
