data "azurerm_resource_group" "opta" {
  name = "opta-${var.env_name}"
}
data "azurerm_subscription" "current" {}
data "azurerm_client_config" "current" {}

data "azurerm_subnet" "opta" {
  name                 = var.private_subnet_name
  resource_group_name  = data.azurerm_resource_group.opta.name
  virtual_network_name = var.vpc_name
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

variable "vpc_name" {
  type = string
}

variable "private_subnet_name" {
  type = string
}

variable "cluster_name" {
  type = string
}

variable "max_nodes" {
  type    = number
  default = 5
}

variable "min_nodes" {
  type    = number
  default = 1
}


variable "node_disk_size" {
  type    = number
  default = 30
}

variable "kubernetes_version" {
  type    = string
  default = "1.21.9"
}

variable "admin_group_object_ids" {
  type    = list(string)
  default = []
}

variable "node_instance_type" {
  type    = string
  default = "Standard_D2_v2"
}

variable "service_cidr" {
  type    = string
  default = "10.0.128.0/20"
}

variable "dns_service_ip" {
  type    = string
  default = "10.0.128.10"
}