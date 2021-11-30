resource "random_id" "key_suffix" {
  byte_length = 8
}

resource "random_password" "root_auth" {
  length      = 20
  min_lower   = 5
  min_upper   = 5
  min_numeric = 5
  special     = false
  lifecycle {
    ignore_changes = [min_lower, min_upper, min_numeric]
  }
}


resource "azurerm_postgresql_server" "opta" {
  name                = "opta-${var.layer_name}-${var.module_name}-${random_id.key_suffix.hex}"
  location            = data.azurerm_resource_group.main.location
  resource_group_name = data.azurerm_resource_group.main.name

  administrator_login          = "postgres"
  administrator_login_password = random_password.root_auth.result

  sku_name   = var.sku_name
  version    = var.engine_version
  storage_mb = 10240

  backup_retention_days        = 7
  geo_redundant_backup_enabled = true
  auto_grow_enabled            = true

  public_network_access_enabled    = false
  ssl_enforcement_enabled          = true
  ssl_minimal_tls_version_enforced = "TLS1_2"
  identity {
    type = "SystemAssigned"
  }

  lifecycle {
    ignore_changes = [storage_mb]
  }
}

resource "azurerm_private_endpoint" "opta" {
  name                = "opta-${var.layer_name}-${var.module_name}"
  location            = data.azurerm_resource_group.main.location
  resource_group_name = data.azurerm_resource_group.main.name
  subnet_id           = data.azurerm_subnet.opta.id

  private_service_connection {
    name                           = "opta-${var.layer_name}-${var.module_name}-${random_id.key_suffix.hex}"
    is_manual_connection           = false
    private_connection_resource_id = azurerm_postgresql_server.opta.id
    subresource_names              = ["postgresqlServer"]
  }
}


resource "azurerm_postgresql_database" "opta" {
  name                = "main"
  resource_group_name = data.azurerm_resource_group.main.name
  server_name         = azurerm_postgresql_server.opta.name
  charset             = "UTF8"
  collation           = "English_United States.1252"
}

resource "azurerm_postgresql_configuration" "log_disconnections" {
  name                = "log_disconnections"
  resource_group_name = data.azurerm_resource_group.main.name
  server_name         = azurerm_postgresql_server.opta.name
  value               = "on"
}


resource "azurerm_postgresql_configuration" "log_duration" {
  name                = "log_duration"
  resource_group_name = data.azurerm_resource_group.main.name
  server_name         = azurerm_postgresql_server.opta.name
  value               = "on"
}


resource "azurerm_postgresql_configuration" "log_retention_days" {
  name                = "log_retention_days"
  resource_group_name = data.azurerm_resource_group.main.name
  server_name         = azurerm_postgresql_server.opta.name
  value               = "5"
}