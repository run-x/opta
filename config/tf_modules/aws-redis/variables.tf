variable "name" {
  type = string
}

variable "node_type" {
  type = string
  default = "cache.m4.large"
}

variable "security_group" {
  type = string
  default = ""
}

variable "subnet_group_name" {
  type = string
  default = "main"
}

variable "redis_version" {
  type = string
  default = "6.0.5"
}

variable "kms_account_key_arn" {
  type = string
}