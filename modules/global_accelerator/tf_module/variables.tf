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

variable "flow_logs_enabled" {
  type = bool
}

variable "flow_logs_bucket" {
  type = string
}

variable "flow_logs_prefix" {
  type = string
}

variable "endpoint_id" {
  type = string
}

variable "enable_auto_dns" {
  type = bool
}

variable "domain" {
  type = string
}

variable "zone_id" {
  type = string
}
