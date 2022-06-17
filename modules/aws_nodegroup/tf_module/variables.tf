data "aws_region" "current" {}

data "aws_eks_cluster" "main" {
  name = "opta-${var.env_name}"
}

locals {
  default_labels = var.ami_type == "AL2_x86_64_GPU" ? {
    node_group_name = "opta-${var.layer_name}-${var.module_name}"
    ami_type        = var.ami_type
    gpu             = true
    } : {
    node_group_name = "opta-${var.layer_name}-${var.module_name}"
    ami_type        = var.ami_type
  }
}

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

variable "max_nodes" {
  type    = number
  default = 15
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

variable "spot_instances" {
  type    = bool
  default = false
}

variable "labels" {
  type    = map(string)
  default = {}
}

variable "taints" {
  type    = list(map(string))
  default = []
}

variable "ami_type" {
  type    = string
  default = "AL2_x86_64"
}

variable "use_gpu" {
  type    = bool
  default = false
}