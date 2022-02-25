data "google_client_config" "current" {}

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

variable "cluster_name" {
  type = string
}

variable "gke_channel" {
  type    = string
  default = "REGULAR"
}

variable "node_zone_names" {
  type = list(string)
}

data "google_secret_manager_secret_version" "kms_suffix" {
  secret = "opta-${var.layer_name}-kms-suffix"
}

data "google_kms_key_ring" "key_ring" {
  name     = "opta-${var.env_name}-${data.google_secret_manager_secret_version.kms_suffix.secret_data}"
  location = data.google_client_config.current.region
}

data "google_kms_crypto_key" "kms" {
  key_ring = data.google_kms_key_ring.key_ring.id
  name     = "opta-${var.env_name}-${data.google_secret_manager_secret_version.kms_suffix.secret_data}"
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
