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

variable "api_key" {
  description = "Datadog API key"
  type        = string
  default     = null
}

variable "values" {
  default = {}
}

variable "timeout" {
  type    = number
  default = 600
}

variable "chart_version" {
  description = "Chart version"
  type        = string
}
