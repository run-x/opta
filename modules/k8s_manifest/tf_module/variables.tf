variable "file_path" {
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

variable "module_name" {
  description = "Module name"
  type        = string
}


variable "host" {}

variable "token" {}

variable "cluster_ca_certificate" {}

variable "client_certificate" {}

variable "client_key" {}

variable "kubeconfig" {}

variable "kubecontext" {}