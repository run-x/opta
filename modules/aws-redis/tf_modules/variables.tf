variable "node_type" {
  type    = string
  default = "cache.m4.large"
}

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

variable "redis_version" {
  type    = string
  default = "6.x"
}

variable "snapshot_window" {
  description = "When should the Snapshot for redis cache be done. UTC Time. Snapshot Retention Limit should be set to more than 0."
  type        = string
  default     = "04:00-05:00"
}

variable "snapshot_retention_limit" {
  description = "Days for which the Snapshot should be retained."
  type        = number
  default     = 0
}
