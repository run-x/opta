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

variable "iam_policy" {
}

variable "extra_iam_policies" {
  type    = list(string)
  default = []
}

variable "links" {
  default = []
}
