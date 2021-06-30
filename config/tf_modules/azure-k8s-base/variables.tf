locals {
  target_ports    = { http : "http", https : "https" }
  container_ports = { http : 80, https : 443 }
  config          = { ssl-redirect : false }
}

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

variable "nginx_high_availability" {
  type    = bool
  default = false
}

variable "linkerd_enabled" {
  type    = bool
  default = true
}

variable "linkerd_high_availability" {
  type    = bool
  default = false
}

variable "delegated" {
  type    = bool
  default = false
}

variable "hosted_zone_name" {
  type    = string
  default = null
}
