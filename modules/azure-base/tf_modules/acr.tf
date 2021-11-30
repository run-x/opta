resource "random_id" "acr_suffix" {
  byte_length = 8
}

resource "azurerm_container_registry" "acr" {
  name                = "opta${random_id.acr_suffix.hex}"
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name
  sku                 = "Premium"

  identity {
    type = "UserAssigned"
    identity_ids = [
      azurerm_user_assigned_identity.acr_uai.id
    ]
  }

  encryption {
    enabled            = true
    key_vault_key_id   = azurerm_key_vault_key.acr.id
    identity_client_id = azurerm_user_assigned_identity.acr_uai.client_id
  }

  depends_on = [azurerm_role_assignment.acr_encryption]

}

resource "azurerm_user_assigned_identity" "acr_uai" {
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name
  name                = "registry-uai"
}

resource "azurerm_role_assignment" "acr_encryption" {
  scope                = azurerm_key_vault.opta.id
  role_definition_name = "Key Vault Crypto Service Encryption User"
  principal_id         = azurerm_user_assigned_identity.acr_uai.principal_id
}