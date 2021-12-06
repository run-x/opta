data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

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

variable "expose_via_domain" {
  type    = bool
  default = false
}

variable "runtime" {
  type = string
}

variable "filename" {
  type = string
}

variable "handler" {
  type    = string
  default = "index.handler"
}

variable "env_vars" {
  type = map(string)
}

variable "extra_iam_policies" {
  type = list(string)
}

variable "vpc_id" {
  type    = string
  default = null
}