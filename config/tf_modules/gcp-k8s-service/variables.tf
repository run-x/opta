data "google_container_registry_repository" "root" {}
data "google_client_config" "current" {}


locals {
  uri_components = [for s in var.public_uri : {
    // We probably don't need the trim anymore but leaving this here for
    // potentional backwards compatibility
    domain : trim(split("/", s)[0], "."),
    pathPrefix : (length(split("/", s)) > 1 ? "/${join("/", slice(split("/", s), 1, length(split("/", s))))}" : "/")
  }]
  env_short    = substr(var.env_name, 0, 9)
  layer_short  = substr(var.layer_name, 0, 9)
  module_short = substr(var.module_name, 0, 9)
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

variable "consistent_hash" {
  type    = string
  default = null
}

variable "sticky_session" {
  default = false
}

variable "sticky_session_max_age" {
  default = 86400
}

variable "port" {
  description = "Port to be exposed as :80"
  type        = map(number)
}

variable "image" {
  description = "External Image to be deployed"
  type        = string
}

variable "tag" {
  description = "Tag of image to be deployed"
  type        = string
  default     = null
}

variable "digest" {
  description = "Digest of image to be deployed"
  type        = string
  default     = null
}

variable "min_containers" {
  description = "Min value for HPA autoscaling"
  type        = string
  default     = 1
}

variable "max_containers" {
  description = "Max value for HPA autoscaling"
  type        = string
  default     = 3
}

variable "autoscaling_target_cpu_percentage" {
  description = "Percentage of requested cpu after which autoscaling kicks in"
  default     = 80
}

variable "autoscaling_target_mem_percentage" {
  description = "Percentage of requested memory after which autoscaling kicks in"
  default     = 80
}

variable "liveness_probe_path" {
  description = "Url path for liveness probe"
  type        = string
  default     = null
}

variable "readiness_probe_path" {
  description = "Url path for readiness probe"
  type        = string
  default     = null
}

variable "healthcheck_path" {
  type    = string
  default = null
}

variable "resource_request" {
  type = map(any)
  default = {
    cpu : 100
    memory : 128
  }
}

variable "env_vars" {
  description = "Environment variables to pass to the container"
  type = list(object({
    name  = string
    value = string
  }))
  default = []
}

variable "public_uri" {
  type    = list(string)
  default = []
}

variable "domain" {
  type    = string
  default = ""
}

variable "secrets" { default = null }
variable "links" { default = null }

variable "link_secrets" {
  type    = list(map(string))
  default = []
}

variable "manual_secrets" {
  type    = list(string)
  default = []
}

variable "read_buckets" {
  type    = list(string)
  default = []
}

variable "write_buckets" {
  type    = list(string)
  default = []
}

variable "keep_path_prefix" {
  type    = bool
  default = false
}

variable "persistent_storage" {
  type    = list(map(string))
  default = []
}
