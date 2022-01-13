variable "file_path" {
  type    = string
  default = "k8test.yaml"
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


variable "kubeconfig" {
  description = "Kubernetes config path"
  type        = string
}
variable "kubecontext" {
  description = "Kubernetes context"
  type        = string
}


