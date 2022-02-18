data "google_client_config" "current" {}

data "google_container_cluster" "main" {
  name     = "opta-${var.layer_name}"
  location = data.google_client_config.current.region
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

variable "gke_channel" {
  type    = string
  default = "REGULAR"
}

variable "node_zone_names" {
  type = list(string)
}

variable "vpc_self_link" {
  type = string
}

variable "private_subnet_self_link" {
  type = string
}

variable "max_nodes" {
  type    = number
  default = 5
}

variable "min_nodes" {
  type    = number
  default = 1
}

variable "k8s_master_ipv4_cidr_block" {
  type = string
}

variable "node_disk_size" {
  type    = number
  default = 20
}

variable "node_instance_type" {
  type    = string
  default = "n2-highcpu-4"
}

variable "preemptible" {
  type    = bool
  default = false
}

variable "taints" {
  type    = list(map(string))
  default = []
}
