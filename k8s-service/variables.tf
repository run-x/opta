data "aws_caller_identity" "current" {}

variable "external_image" {
  description = "Using an external image, or do we need to create an ecr repository?"
  type = bool
  default = false
}

variable "name" {
  description = "Name of the k8s service"
  type = string
}

variable "namespace" {
  description = "Namespace for these resources"
  type = string
  default = "default"
}

variable "target_port" {
  description = "Port to be exposed as :80"
  type = number
}

variable "image" {
  description = "Image to be deployed"
  type = string
  default = "nginx"
}

variable "tag" {
  description = "Tag of image to be deployed"
  type = string
  default = "latest"
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

variable "autoscaling_cpu_percentage_threshold" {
  description = "Percentage of requested cpu after which autoscaling kicks in"
  default = 80
}

variable "autoscaling_mem_percentage_threshold" {
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

variable "pod_resource_limits" {
  description = "Resource limits for pod"
  default = {
    cpu = "200m"
    memory = "256Mi"
  }
  type = map
}

variable "pod_resource_requests" {
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

variable "domain" {
  type = string
  default = ""
}

variable "uri_prefix" {
  type = string
  default = "/"
}
