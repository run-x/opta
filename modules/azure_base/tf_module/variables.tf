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

variable "private_ipv4_cidr_block" {
  description = "Cidr block for private subnet. Don't need to worry about AZs in Azure"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_ipv4_cidr_block" {
  description = "Cidr block for private subnet. Don't need to worry about AZs in Azure"
  type        = string
  default     = "10.0.0.0/17"
}

variable "location" {
  type = string
}