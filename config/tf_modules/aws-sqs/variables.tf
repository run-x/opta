data "aws_caller_identity" "current" {}

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

variable "fifo" {
  type    = bool
  default = false
}

variable "content_based_deduplication" {
  type    = bool
  default = false
}

variable "delay_seconds" {
  type    = number
  default = 0
}

variable "message_retention_seconds" {
  type    = number
  default = 345600
}

variable "receive_wait_time_seconds" {
  type    = number
  default = 0
}
