locals {
  target_ports    = { http : "http", https : "https" }
  container_ports = { http : 80, https : 443 }
  //  https://github.com/kubernetes/ingress-nginx/issues/4628
  config = merge({ ssl-redirect : var.private_key == "" ? false : true
  force-ssl-redirect : var.private_key == "" ? false : true }, var.nginx_config)
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

variable "private_key" {
  type    = string
  # Ignore since this default value is never used, its for a logical if condition checking if user specified no private_key only.
  #tfsec:ignore:general-secrets-no-plaintext-exposure
  default = ""
}

variable "certificate_body" {
  type    = string
  default = ""
}

variable "certificate_chain" {
  type    = string
  default = ""
}


variable "nginx_config" {
  default = {}
}

variable "cert_manager_values" {
  default = {}
}

variable "linkerd_values" {
  default = {}
}

variable "ingress_nginx_values" {
  default = {}
}