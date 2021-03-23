locals {
  target_ports = var.delegated ? { http: "http", https: "http" } : { http: "http" }
  container_ports = var.delegated == "" ? { http: 80, https: 443 } : { http: 80, https: 443 }
  config = { ssl-redirect: false }
  annotations = var.delegated? "{\"exposed_ports\": {\"80\":{\"name\": \"opta-${var.layer_name}-http\"}, \"443\":{\"name\": \"opta-${var.layer_name}-https\"}}}" : "{\"exposed_ports\": {\"80\":{\"name\": \"opta-${var.layer_name}-http\"}}}"
}

data "google_client_config" "current" {}

data "google_container_cluster" "main" {
  name = "opta-${var.env_name}"
  location = data.google_client_config.current.region
}

variable "env_name" {
  description = "Env name"
  type = string
}

variable "layer_name" {
  description = "Layer name"
  type        = string
}

variable "module_name" {
  description = "Module name"
  type = string
}

variable "domain" {
  type = string
  default = ""
}

variable "delegated" {
  type = bool
}

variable "high_availability" {
  type = bool
  default = true
}
