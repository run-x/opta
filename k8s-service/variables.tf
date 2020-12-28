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

variable "public_ip_name" {
  description = "IP address name to attach to this service"
  type = string
  default = ""
}

variable "replicas" {
  description = "Number of replicas to run"
  type = number
  default = 1
}

variable "image" {
  description = "Image to be deployed"
  type = string
}

variable "env_vars" {
  description = "Environment variables to pass to the container"
  type = list(object({
    name = string
    value = string
  }))
}
