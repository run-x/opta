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

variable "read_capacity" {
  type    = number
  default = 20
}

variable "write_capacity" {
  type    = number
  default = 20
}

variable "billing_mode" {
  type    = string
  default = "PROVISIONED"
}

variable "hash_key" {
  type    = string
  default = ""
}

variable "range_key" {
  type    = string
  default = null
}

variable "attributes" {
  type = list(map(string))
}