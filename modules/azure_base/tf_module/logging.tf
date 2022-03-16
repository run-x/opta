resource "random_id" "logging_suffix" {
  byte_length = 4
}

resource "azurerm_storage_account" "infra_logging" {
  name                      = "optainfralogs${random_id.logging_suffix.hex}"
  location                  = data.azurerm_resource_group.opta.location
  resource_group_name       = data.azurerm_resource_group.opta.name
  account_replication_type  = "LRS"
  account_tier              = "Standard"
  enable_https_traffic_only = true
  min_tls_version           = "TLS1_2"
  network_rules {
    default_action = "Deny"
    bypass         = ["AzureServices"]
  }
}

resource "azurerm_monitor_diagnostic_setting" "infra_logging" {
  name               = "opta-${var.env_name}"
  target_resource_id = azurerm_key_vault.opta.id
  storage_account_id = azurerm_storage_account.infra_logging.id

  log {
    category = "AuditEvent"
    enabled  = true

    retention_policy {
      enabled = true
      days    = 180
    }
  }

  log {
    category = "AzurePolicyEvaluationDetails"
    enabled  = false

    retention_policy {
      days    = 0
      enabled = false
    }
  }

  metric {
    category = "AllMetrics"

    retention_policy {
      enabled = false
    }
  }
}

data "azurerm_network_watcher" "default" {
  name                = "NetworkWatcher_${data.azurerm_resource_group.opta.location}"
  resource_group_name = "NetworkWatcherRG"
  depends_on          = [azurerm_virtual_network.opta]
}

resource "azurerm_log_analytics_workspace" "watcher" {
  name                = "opta-${var.env_name}"
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name
  sku                 = "PerGB2018"
}

resource "azurerm_network_watcher_flow_log" "vpc_flow_log" {
  name                 = "opta-${var.env_name}"
  location             = data.azurerm_resource_group.opta.location
  network_watcher_name = data.azurerm_network_watcher.default.name
  resource_group_name  = "NetworkWatcherRG"

  network_security_group_id = azurerm_network_security_group.opta.id
  storage_account_id        = azurerm_storage_account.infra_logging.id
  enabled                   = true

  retention_policy {
    enabled = true
    days    = 90
  }

  traffic_analytics {
    enabled               = true
    workspace_id          = azurerm_log_analytics_workspace.watcher.workspace_id
    workspace_region      = azurerm_log_analytics_workspace.watcher.location
    workspace_resource_id = azurerm_log_analytics_workspace.watcher.id
    interval_in_minutes   = 10
  }
}