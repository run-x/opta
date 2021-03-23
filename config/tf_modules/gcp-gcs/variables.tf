data "google_client_config" "current" {}

data "google_kms_key_ring" "key_ring" {
  name     = "opta-${var.layer_name}"
  location = data.google_client_config.current.region
}

data "google_kms_crypto_key" "kms" {
  key_ring = data.google_kms_key_ring.key_ring.self_link
  name = "opta-${var.layer_name}"
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

variable "bucket_name" {
  type = string
}

variable "block_public" {
  type = bool
  default = true
}
