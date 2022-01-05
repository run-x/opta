data "google_client_config" "current" {}

data "google_secret_manager_secret_version" "kms_suffix" {
  secret = "opta-${var.env_name}-kms-suffix"
}

data "google_kms_key_ring" "key_ring" {
  name     = "opta-${var.env_name}-${data.google_secret_manager_secret_version.kms_suffix.secret_data}"
  location = data.google_client_config.current.region
}

data "google_kms_crypto_key" "kms" {
  key_ring = data.google_kms_key_ring.key_ring.id
  name     = "opta-${var.env_name}-${data.google_secret_manager_secret_version.kms_suffix.secret_data}"
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

variable "bucket_name" {
  type = string
}

variable "block_public" {
  type    = bool
  default = true
}
