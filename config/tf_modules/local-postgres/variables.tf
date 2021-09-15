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

variable "db_user" {
  description = "Database username"
  type = string
  default = "postgres"
}

variable "db_password" {
  description = "Database password"
  type = string
  default = "pgpassword"
}
variable "db_name" {
  description = "Database name"
  type = string
  default = "appdb"
}
