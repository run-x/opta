variable "name" {
  type = string
}

variable "subnet_group_name" {
  type = string
  default = "main-docdb"
}

variable "engine_version" {
  type = string
  default = "4.0.0"
}

variable "security_group" {
  type = string
  default = ""
}

variable "instance_class" {
  type = string
  default = "db.r5.large"
}

variable "kms_account_key_arn" {
  type = string
}
