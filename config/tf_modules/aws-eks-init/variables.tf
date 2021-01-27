data "aws_region" "current" {}

variable "cluster_name" {
  type = string
}

variable "k8s_version" {
  type    = string
  default = "1.18"
}

variable "subnet_ids" {
  type = list(string)
}

variable "key_arn" {
  description = "KMS key to use for disk encryption"
  type        = string
}

variable "control_plane_security_groups" {
  description = "List of security groups to give control plane access to"
  type        = list(string)
  default     = []
}
