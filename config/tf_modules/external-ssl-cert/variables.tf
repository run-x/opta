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

variable "private_key" {
  type = string
}

variable "certificate_body" {
  type = string
}

variable "certificate_chain" {
  type = string
}

variable "domain" {
  type = string
}
