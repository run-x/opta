data "aws_caller_identity" "current" {}
data "aws_availability_zones" "current" {}
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

variable "vpc_log_retention" {
  type    = number
  default = 90
}

variable "total_ipv4_cidr_block" {
  description = "Cidr block to reserve for whole vpc"
  type        = string
  default     = "10.0.0.0/16"
}

variable "private_ipv4_cidr_blocks" {
  description = "Cidr blocks for private subnets. One for each desired AZ"
  type        = list(string)
  default = [
    "10.0.128.0/21",
    "10.0.136.0/21",
    "10.0.144.0/21"
  ]
}

variable "public_ipv4_cidr_blocks" {
  description = "Cidr blocks for public subnets. One for each desired AZ"
  type        = list(string)
  default = [
    "10.0.0.0/21",
    "10.0.8.0/21",
    "10.0.16.0/21"
  ]
}

variable "vpc_id" {
  description = "The ID of an pre-existing VPC to use instead of creating a new VPC for opta"
  type        = string
  default     = null
}

variable "public_subnet_ids" {
  description = "List of pre-existing public subnets to use instead of creating new subnets for opta. Required when var.vpc_id is set."
  type        = list(string)
  default     = null
}

variable "private_subnet_ids" {
  description = "List of pre-existing private subnets to use instead of creating new subnets for opta. Required when var.vpc_id is set."
  type        = list(string)
  default     = null
}
