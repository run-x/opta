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

variable "kubernetes_trusts" {
  type = list(object({
    open_id_url  = string
    open_id_arn  = string
    service_name = string
    namespace    = string
  }))
  default = []
}

variable "allowed_iams" {
  type    = list(string)
  default = []
}

variable "iam_policy" {
}

variable "extra_iam_policies" {
  type    = list(string)
  default = []
}

variable "allowed_k8s_services" {
  default = []
}

variable "links" {
  default = []
}
