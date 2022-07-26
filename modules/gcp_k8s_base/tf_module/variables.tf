locals {
  target_ports    = { http : "http", https : "https" }
  container_ports = { http : 80, https : 443, healthcheck : 10254 }
  config          = merge({ ssl-redirect : false }, var.nginx_config)
  annotations     = "{\"exposed_ports\": { \"443\":{\"name\": \"opta-${var.layer_name}-https\"}}}"
  negs            = formatlist("https://www.googleapis.com/compute/v1/projects/%s/zones/%s/networkEndpointGroups/opta-%s-https", data.google_client_config.current.project, var.zone_names, var.layer_name)
}

data "google_client_config" "current" {}

data "google_container_cluster" "main" {
  name     = "opta-${var.env_name}"
  location = data.google_client_config.current.region
}
data "google_compute_network" "vpc" {
  name = "opta-${var.layer_name}"
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

variable "cert_self_link" {
  type    = string
  default = null
}

variable "hosted_zone_name" {
  type    = string
  default = ""
}

variable "domain" {
  type    = string
  default = null
}

variable "zone_names" {
  type    = list(string)
  default = []
}
variable "private_key" {
  type = string
  # Ignore since this default value is never used, its for a logical if condition checking if user specified no private_key only.
  #tfsec:ignore:general-secrets-no-plaintext-exposure
  default = ""
}

variable "certificate_body" {
  type = string
  # Ignore since this default value is never used, its for a logical if condition checking if user specified no cert.
  #tfsec:ignore:general-secrets-no-plaintext-exposure
  default = ""
}

variable "certificate_chain" {
  type    = string
  default = ""
}

variable "nginx_config" {
  default = {}
}

variable "expose_self_signed_ssl" {
  type    = bool
  default = false
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

variable "nginx_enabled" {
  type = bool
}