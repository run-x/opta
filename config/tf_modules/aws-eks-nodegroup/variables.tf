data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
data "aws_eks_cluster" "current" {
  name = var.cluster_name
}

variable "cluster_name" {
  type = string
}

variable "node_group_name" {
  type = string
}

variable "disk_size" {
  type    = number
  default = 20
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}

variable "use_gpu" {
  type    = bool
  default = false
}

variable "node_labels" {
  type    = map(string, )
  default = {}
}

variable "max_size" {
  type    = number
  default = 3
}

variable "min_size" {
  type    = number
  default = 1
}

variable "desired_size" {
  type    = number
  default = 1
}

variable "ssh_key" {
  type    = string
  default = ""
}

variable "ssh_security_group_ids" {
  type    = list(string)
  default = []
}
