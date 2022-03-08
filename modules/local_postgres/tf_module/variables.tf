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
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Database password"
  type        = string
  # Ignore since local is within PC, not designed to secure secrets.
  #tfsec:ignore:general-secrets-no-plaintext-exposure
  default = "pgpassword"
}
variable "db_name" {
  description = "Database name"
  type        = string
  default     = "appdb"
}

variable "paasns" {
  description = "A string like pass_myorg_my_layer, used to have multiple paas helm charts"
  type        = string
  default     = "paas"
}