data "google_container_registry_repository" "root" {}
data "google_client_config" "current" {}


locals {
  layer_short  = substr(replace(var.layer_name, "-", ""), 0, 12)
  module_short = substr(replace(var.module_name, "-", ""), 0, 12)
  get_buckets  = toset(concat(var.read_buckets, var.write_buckets))
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
