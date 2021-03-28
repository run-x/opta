data "google_client_config" "current" {}

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

variable "gke_channel" {
  type = string
  default = "REGULAR"
}

data "google_kms_key_ring" "key_ring" {
  name     = "opta-${var.layer_name}"
  location = data.google_client_config.current.region
}

data "google_kms_crypto_key" "kms" {
  key_ring = data.google_kms_key_ring.key_ring.self_link
  name = "opta-${var.layer_name}"
}

data "google_compute_network" "vpc" {
  name = "opta-${var.layer_name}"
}

data "google_compute_subnetwork" "private" {
  name = "opta-${var.layer_name}-${data.google_client_config.current.region}-private"
}


variable "max_nodes" {
  type    = number
  default = 5
}

variable "min_nodes" {
  type    = number
  default = 1
}


variable "node_disk_size" {
  type    = number
  default = 20
}

variable "node_instance_type" {
  type    = string
  default = "n2-highcpu-4"
}
