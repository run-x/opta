data "aws_caller_identity" "current" {}

locals {
  public_uri_parts = split("/", var.public_uri)
  domain = var.domain == ""? public_uri_parts[0] : var.domain
  path_prefix = length(public_uri_parts) > 1? join("/",slice(public_uri_parts, 1, length(public_uri_parts)-1)) : "/"
}

variable "k8s_openid_provider_url" {
  type = string
}

variable "k8s_openid_provider_arn" {
  type = string
}


variable "name" {
  description = "Name of the k8s service"
  type = string
}

variable "layer_name" {
  type = string
}

variable "module_name" {
  type = string
}

variable "port" {
  description = "Port to be exposed as :80"
  type = map(number)
}

variable "image" {
  description = "External Image to be deployed"
  type = string
  default = null
}

variable "tag" {
  description = "Tag of image to be deployed"
  type = string
  default = null
}

variable "min_autoscaling" {
  description = "Min value for HPA autoscaling"
  type = string
  default = 1
}

variable "max_autoscaling" {
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

variable "container_resource_limits" {
  description = "Resource limits for pod"
  default = {
    cpu = "200m"
    memory = "256Mi"
  }
  type = map
}

variable "container_resource_requests" {
  description = "Request requests for pod"
  default = {
    cpu = "100m"
    memory = "128Mi"
  }
  type = map
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

variable "iam_policy" {
}

variable "additional_iam_roles" {
  type = list(string)
  default = []
}
