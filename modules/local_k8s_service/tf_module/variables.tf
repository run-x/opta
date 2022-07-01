# data "aws_caller_identity" "current" {}

locals {
  uri_components = [for s in var.public_uri : {
    domain : split("/", s)[0],
    pathPrefix : (length(split("/", s)) > 1 ? "/${join("/", slice(split("/", s), 1, length(split("/", s))))}" : "/"),
    pathPrefixName : replace((length(split("/", s)) > 1 ? "/${join("/", slice(split("/", s), 1, length(split("/", s))))}" : "/"), "/", "")
  }]
  image           = local.uppercase_image == "AUTO" ? (var.digest != null ? "${var.local_registry_name}/${var.layer_name}/${var.module_name}@${var.digest}" : (var.tag == null ? "" : "${var.local_registry_name}/${var.layer_name}/${var.module_name}:${var.tag}")) : (var.tag == null ? var.image : "${var.image}:${var.tag}")
  uppercase_image = upper(var.image)
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

variable "ports" {
  description = "Ports to be exposed"
  type        = list(any)
}

variable "http_port" {
  description = "The port that exposes an HTTP interface"
  type        = any
  default     = null
}

variable "probe_port" {
  description = "The port that is used for health probes"
  type        = any
  default     = null
}

variable "service_annotations" {
  description = "Annotations to add to the service resource"
  type        = map(string)
  default     = {}
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

variable "resource_limits" {
  type = map(any)
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

variable "local_registry_name" {
  type    = string
  default = "localhost:5000"
}

variable "keep_path_prefix" {
  type    = bool
  default = false
}

variable "persistent_storage" {
  type    = list(map(string))
  default = []
}

variable "initial_liveness_delay" {
  type    = number
  default = 30
}

variable "initial_readiness_delay" {
  type    = number
  default = 30
}

variable "ingress_extra_annotations" {
  type    = map(string)
  default = {}
}

variable "tolerations" {
  type    = list(map(string))
  default = []
}

variable "cron_jobs" {
  default = []
}

variable "max_history" {
  type = number
}

variable "commands" {
  type = list(string)
}

variable "args" {
  type = list(string)
}