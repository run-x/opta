locals {
  values_from_files = [for x in var.values_files :
    file(x)
  ]
}

variable "repository" {
  type    = string
  default = null
}

variable "chart" {
  type = string
}

variable "namespace" {
  type    = string
  default = "default"
}

variable "create_namespace" {
  type    = bool
  default = false
}

variable "atomic" {
  type    = bool
  default = true
}

variable "wait" {
  type    = bool
  default = true
}

variable "wait_for_jobs" {
  type    = bool
  default = false
}

variable "cleanup_on_fail" {
  type    = bool
  default = true
}

variable "chart_version" {
  type    = string
  default = null
}

variable "values_files" {
  type    = list(string)
  default = []
}

variable "values_file" {
  type    = string
  default = null
}

variable "values" {
  default = {}
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

variable "timeout" {
  type    = number
  default = 300
}

variable "dependency_update" {
  type    = bool
  default = true
}

variable "max_history" {
  type = number
}

variable "release_name" {}
