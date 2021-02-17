variable "name" {
  type = string
}

variable "subnet_group_name" {
  type = string
  default = ""
}

variable "engine" {
  type = string
  default = "aurora-postgresql"
}

variable "engine_version" {
  type = string
  default = "11.9"
}

variable "security_group" {
  type = string
  default = ""
}

variable "instance_class" {
  type = string
  default = "db.t3.medium"
}
