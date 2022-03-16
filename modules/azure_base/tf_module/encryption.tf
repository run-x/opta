resource "random_id" "key_suffix" {
  byte_length = 8
}

resource "azurerm_key_vault" "opta" {
  name                            = "opta-${random_id.key_suffix.hex}"
  location                        = data.azurerm_resource_group.opta.location
  resource_group_name             = data.azurerm_resource_group.opta.name
  tenant_id                       = data.azurerm_subscription.current.tenant_id
  enable_rbac_authorization       = true
  sku_name                        = "premium"
  enabled_for_disk_encryption     = true
  enabled_for_deployment          = true
  enabled_for_template_deployment = true
  purge_protection_enabled        = true
  lifecycle {
    ignore_changes = [location]
  }
  network_acls {
    bypass         = "AzureServices"
    default_action = "Deny"
  }
}

resource "azurerm_key_vault_key" "acr" {
  name         = "opta-${var.env_name}-acr"
  key_vault_id = azurerm_key_vault.opta.id
  key_type     = "RSA"
  key_size     = 2048

  key_opts = [
    "decrypt",
    "encrypt",
    "sign",
    "unwrapKey",
    "verify",
    "wrapKey",
  ]
}
