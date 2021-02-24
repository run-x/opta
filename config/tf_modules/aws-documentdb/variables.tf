variable "env_name" {
  description = "Env name"
  type = string
}

variable "layer_name" {
  description = "Layer name"
  type        = string
}

variable "module_name" {
  description = "Module name"
  type = string
}

variable "engine_version" {
  type = string
  default = "4.0.0"
}

variable "instance_class" {
  type = string
  default = "db.r5.large"
}
