resource "azurerm_user_assigned_identity" "opta" {
  name                = "aks-example-identity"
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name
  lifecycle {
    ignore_changes = [
      location
    ]
  }
}

resource "azurerm_role_assignment" "opta" {
  scope                = data.azurerm_subnet.opta.id
  role_definition_name = "Network Contributor"
  principal_id         = azurerm_user_assigned_identity.opta.principal_id
}

resource "azurerm_role_assignment" "azurerm_container_registry" {
  scope                = data.azurerm_resource_group.opta.id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_user_assigned_identity.opta.principal_id
}


resource "azurerm_kubernetes_cluster" "main" {
  name                = "opta-${var.layer_name}"
  location            = data.azurerm_resource_group.opta.location
  resource_group_name = data.azurerm_resource_group.opta.name
  dns_prefix          = "opta"
  //  disk_encryption_set_id = azurerm_disk_encryption_set.opta.id
  kubernetes_version = var.kubernetes_version

  network_profile {
    network_plugin     = "azure"
    network_policy     = "calico"
    service_cidr       = var.service_cidr
    dns_service_ip     = var.dns_service_ip
    docker_bridge_cidr = "172.17.0.1/16"
  }

  role_based_access_control {
    enabled = true
    azure_active_directory {
      managed                = true
      tenant_id              = data.azurerm_client_config.current.tenant_id
      admin_group_object_ids = var.admin_group_object_ids
    }
  }

  default_node_pool {
    name                = "default"
    node_count          = var.min_nodes
    vm_size             = var.node_instance_type
    enable_auto_scaling = true
    max_count           = var.max_nodes
    min_count           = var.min_nodes
    vnet_subnet_id      = data.azurerm_subnet.opta.id
  }

  identity {
    type                      = "UserAssigned"
    user_assigned_identity_id = azurerm_user_assigned_identity.opta.id
  }

  lifecycle {
    ignore_changes = [
      default_node_pool["node_count"],
      location
    ]
  }

  depends_on = [
    azurerm_role_assignment.opta,
  ]
}