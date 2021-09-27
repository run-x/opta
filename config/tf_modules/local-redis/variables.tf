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

variable "paasns" {
  description = "A string like pass_myorg_my_layer, used to have multiple paas helm charts"
  type        = string
  default     = "paas"
}