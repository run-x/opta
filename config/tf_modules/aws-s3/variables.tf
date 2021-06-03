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

variable "bucket_name" {
  type = string
}

variable "block_public" {
  type    = bool
  default = true
}

variable "bucket_policy" {
  type    = map(any)
  default = null
}

