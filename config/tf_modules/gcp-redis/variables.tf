data "google_compute_network" "vpc" {
  name = "opta-${var.env_name}"
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
  default = "REDIS_5_0"
}

variable "high_availability" {
  type    = bool
  default = true
}

variable "memory_size_gb" {
  type    = number
  default = 2
}
