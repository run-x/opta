data "azurerm_resource_group" "main" {
  name = "opta-${var.env_name}"
}

data "azurerm_subnet" "opta" {
  name                 = "opta-${var.env_name}-subnet"
  resource_group_name  = data.azurerm_resource_group.main.name
  virtual_network_name = "opta-${var.env_name}"
}

variable "env_name" {
  description = "Env name"
  type        = string
}

variable "layer_name" {
  description = "Layer name"
  type        = string
}

variable "module_name" {
  description = "Module name"
  type        = string
}

variable "engine_version" {
  type    = string
  default = "11"
}

variable "sku_name" {
  type    = string
  default = "GP_Gen5_2"
}
