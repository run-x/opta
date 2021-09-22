variable "node_type" {
  type    = string
  default = "cache.m4.large"
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

variable "redis_version" {
  type    = string
  default = "6.x"
}
