data "google_client_config" "current" {}

locals {
  full_subdomains = formatlist("%s.${var.domain}", var.subdomains)
}

variable "domain" {
  type = string
}

variable "subdomains" {
  type    = list(string)
  default = []
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

variable "delegated" {
  type    = bool
  default = false
}

data "google_compute_network" "vpc" {
  name = "opta-${var.layer_name}"
}

data "google_compute_subnetwork" "private" {
  name = "opta-${var.layer_name}-${data.google_client_config.current.region}-private"
}