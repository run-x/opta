data "aws_region" "current" {}

data "aws_kms_key" "env_key" {
  key_id = var.kms_account_key_arn
}

variable "kms_account_key_arn" {
  type = string
}

variable "private_subnet_ids" {
  type = list(string)
}

variable "vpc_id" {
  type = string
}

variable "env_name" {
  description = "Env name"
  type        = string
}

variable "layer_name" {
  description = "Layer name"
  type        = string
}

variable "enable_metrics" {
  type = bool
}

variable "module_name" {
  description = "Module name"
  type        = string
}

variable "max_nodes" {
  type    = number
  default = 5
}

variable "min_nodes" {
  type    = number
  default = 3
}

variable "node_disk_size" {
  type    = number
  default = 20
}

variable "node_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "k8s_version" {
  type    = string
  default = "1.18"
}

variable "spot_instances" {
  type    = bool
  default = false
}

variable "control_plane_security_groups" {
  description = "List of security groups to give control plane access to"
  type        = list(string)
  default     = []
}

variable "node_launch_template" {
  default = {}
  type    = map(string)
}
