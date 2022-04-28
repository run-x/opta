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

variable "vpc_id" {
  type = string
}

variable "kms_account_key_arn" {
  type = string
}

variable "client_cidr_block" {
  type = string
}

variable "public_subnets_ids" {
  type = list(string)
}