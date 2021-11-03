data "google_container_registry_repository" "root" {}
data "google_client_config" "current" {}


locals {
  env_short    = substr(replace(var.env_name, "-", ""), 0, 9)
  layer_short  = substr(replace(var.layer_name, "-", ""), 0, 9)
  module_short = substr(replace(var.module_name, "-", ""), 0, 9)
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

variable "read_buckets" {
  type    = list(string)
  default = []
}

variable "write_buckets" {
  type    = list(string)
  default = []
}

variable "allowed_k8s_services" {
  default = []
}

variable "links" {
  default = []
}

variable "additional_iam_roles" {
  default = []
}

variable "explicit_name" {
  type    = string
  default = null
}
