data "aws_caller_identity" "current" {}

locals {
  uri_components = [for s in var.public_uri: {
    domain: split("/", s)[0],
    pathPrefix: (length(split("/", s)) > 1 ? "/${join("/",slice(split("/", s), 1, length(split("/", s))))}" : "/")
  }]
}

variable "openid_provider_url" {
  type = string
}

variable "openid_provider_arn" {
  type = string
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
  type = list(string)
  default = []
}

variable "domain" {
  type = string
  default = ""
}

variable "secrets" {
  type = list(map(string))
  default = []
}

variable "iam_policy" {
}

variable "additional_iam_roles" {
  type = list(string)
  default = []
}
