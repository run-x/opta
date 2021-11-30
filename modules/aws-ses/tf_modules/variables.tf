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

variable "domain" {
  type = string
}

variable "zone_id" {
  type = string
}

variable "mail_from_prefix" {
  type    = string
  default = "mail"
}
