data "google_client_config" "current" {}
data "google_project" "current" {}
data "google_storage_project_service_account" "gcs_account" {}

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

variable "private_ipv4_cidr_block" {
  description = "Cidr block for private subnet. Don't need to worry about AZs in GCP"
  type        = string
  default     = "10.0.0.0/19"
}

variable "cluster_ipv4_cidr_block" {
  type    = string
  default = "10.0.32.0/19"
}

variable "services_ipv4_cidr_block" {
  type    = string
  default = "10.0.64.0/20"
}

variable "k8s_master_ipv4_cidr_block" {
  type    = string
  default = "10.0.80.0/28"
}
