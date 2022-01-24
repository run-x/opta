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

variable "engine_version" {
  type    = string
  default = "4.0.0"
}

variable "instance_class" {
  type    = string
  default = "db.r5.large"
}

variable "instance_count" {
  type        = number
  default     = 1
  description = "Number of Instances for aws_docdb_cluster_instance"
}
variable "deletion_protection" {
  type        = bool
  default     = false
  description = "A value that indicates whether the DB cluster has deletion protection enabled. The database can't be deleted when deletion protection is enabled."
}
