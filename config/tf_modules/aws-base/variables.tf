data "aws_caller_identity" "current" {}
data aws_availability_zones "current" {}

data "external" "throw_error" {
  count = var.env_name == var.layer_name ? 0 : 1
  program = ["echo 'aws_base can only be run at the base/env opta yaml'", ""]
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

variable "total_ipv4_cidr_block" {
  description = "Cidr block to reserve for whole vpc"
  type        = string
  default = "10.0.0.0/16"
}

variable "private_ipv4_cidr_blocks" {
  description = "Cidr blocks for private subnets. One for each desired AZ"
  type        = list(string)
  default     = [
    "10.0.128.0/21",
    "10.0.136.0/21",
    "10.0.144.0/21"
  ]
}

variable "public_ipv4_cidr_blocks" {
  description = "Cidr blocks for public subnets. One for each desired AZ"
  type        = list(string)
  default     = [
    "10.0.0.0/21",
    "10.0.8.0/21",
    "10.0.16.0/21"
  ]
}

variable "subnet_tags" {
  type    = map(string)
  default = {}
}
