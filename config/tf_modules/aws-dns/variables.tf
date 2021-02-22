data "external" "throw_error" {
  count = var.env_name == var.layer_name ? 0 : 1
  program = ["echo 'aws_base can only be run at the base/env opta yaml'", ""]
}

variable "domain" {
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

variable "delegated" {
  type = bool
  default = false
}
