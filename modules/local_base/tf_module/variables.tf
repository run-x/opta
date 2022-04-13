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

variable "local_k8s_cluster_name" {
  type        = string
  default     = "kind-opta-local-cluster"
  description = "The name of the local K8s cluster"
}