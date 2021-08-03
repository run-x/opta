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

variable "engine_version" {
  type    = string
  default = "11.9"
}

variable "instance_class" {
  type    = string
  default = "db.t3.medium"
}

variable "safety" {
  type    = bool
  default = false
}

variable "multi_az" {
  type = bool
  default = false
}
