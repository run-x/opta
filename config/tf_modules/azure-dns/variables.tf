data "azurerm_subscription" "current" {}
data "azurerm_resource_group" "opta" {
  name = "opta-${var.env_name}"
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

variable "domain" {
  type = string
}

variable "delegated" {
  type    = bool
  default = false
}