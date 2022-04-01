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

variable "backup_retention_days" {
  description = "How many days to keep the backup retention"
  type        = number
}

variable "engine_version" {
  type    = string
  default = "5.7.mysql_aurora.2.04.2"
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
  type    = bool
  default = false
}

variable "db_name" {
  type    = string
  default = "app"
}