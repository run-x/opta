locals {
  target_ports = var.cert_arn == "" ? { http: "http" } : { http: "http", https: "http" }
}

data "external" "throw_error" {
  count = var.env_name == var.layer_name ? 0 : 1
  program = ["echo 'aws_base can only be run at the base/env opta yaml'", ""]
}

data "aws_eks_cluster" "main" {
  name = "opta-${var.env_name}"
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

variable "domain" {
  type = string
  default = ""
}

variable "cert_arn" {
  type = string
  default = ""
}

variable "openid_provider_url" {
  type = string
}

variable "openid_provider_arn" {
  type = string
}
