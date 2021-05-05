locals {
  target_ports = var.delegated ? { http: "http", https: "https" } : { http: "http" }
  container_ports = { http: 80, https: 443 }
  config = { ssl-redirect: false }
  annotations = "{\"exposed_ports\": { \"443\":{\"name\": \"opta-${var.layer_name}-https\"}}}"
  negs = formatlist("https://www.googleapis.com/compute/v1/projects/%s/zones/%s/networkEndpointGroups/opta-%s-https", data.google_client_config.current.project, var.zone_names, var.layer_name)
}

data "google_client_config" "current" {}

data "google_container_cluster" "main" {
  name = "opta-${var.env_name}"
  location = data.google_client_config.current.region
}
data "google_compute_network" "vpc" {
  name = "opta-${var.layer_name}"
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

variable "high_availability" {
  type = bool
  default = true
}

variable "delegated" {
  type = bool
  default = false
}

variable "cert_self_link" {
  type = string
  default = null
}

variable "hosted_zone_name" {
  type = string
  default = null
}

variable "zone_names" {
  type = list(string)
  default = []
}
