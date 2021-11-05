data "aws_caller_identity" "current" {}

locals {
  uri_components = [for s in var.public_uri : {
    domain : split("/", s)[0],
    pathPrefix : (length(split("/", s)) > 1 ? "/${join("/", slice(split("/", s), 1, length(split("/", s))))}" : "/")
  }]
  uppercase_image = upper(var.image)
}

variable "openid_provider_url" {
  type = string
}

variable "openid_provider_arn" {
  type = string
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

variable "iam_policy" {
}

variable "additional_iam_policies" {
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

variable "ingress_extra_annotations" {
  type    = map(string)
  default = {}
}
