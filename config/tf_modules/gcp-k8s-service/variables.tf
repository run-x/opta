data "google_container_registry_repository" "root" {}
data "google_client_config" "current" {}


locals {
  public_uri_parts = split("/", var.public_uri)
  domain = var.domain == ""? local.public_uri_parts[0] : var.domain
  path_prefix = length(local.public_uri_parts) > 1 ? "/${join("/",slice(local.public_uri_parts, 1, length(local.public_uri_parts)))}" : "/"
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

variable "port" {
  description = "Port to be exposed as :80"
  type = map(number)
}

variable "image" {
  description = "External Image to be deployed"
  type = string
}

variable "tag" {
  description = "Tag of image to be deployed"
  type = string
  default = null
}

variable "min_containers" {
  description = "Min value for HPA autoscaling"
  type = string
  default = 1
}

variable "max_containers" {
  description = "Max value for HPA autoscaling"
  type = string
  default = 3
}

variable "autoscaling_target_cpu_percentage" {
  description = "Percentage of requested cpu after which autoscaling kicks in"
  default = 80
}

variable "autoscaling_target_mem_percentage" {
  description = "Percentage of requested memory after which autoscaling kicks in"
  default = 80
}

variable "liveness_probe_path" {
  description = "Url path for liveness probe"
  type = string
  default = "/healthcheck"
}

variable "readiness_probe_path" {
  description = "Url path for readiness probe"
  type = string
  default = "/healthcheck"
}

variable "healthcheck_path" {
  type = string
  default = null
}

variable "resource_request" {
  type = map
  default = {
    cpu: 100
    memory: 128
  }
}

variable "env_vars" {
  description = "Environment variables to pass to the container"
  type = list(object({
    name = string
    value = string
  }))
  default = []
}

variable "public_uri" {
  type = string
  default = ""
}

variable "domain" {
  type = string
  default = ""
}

variable "secrets" {
  type = list(map(string))
  default = []
}

variable "read_buckets" {
  type = list(string)
  default = []
}

variable "write_buckets" {
  type = list(string)
  default = []
}
