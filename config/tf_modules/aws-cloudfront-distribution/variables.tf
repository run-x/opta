locals {
  s3_origin_id = "optaDefaultOriginId"
  allowed_methods = var.access_type == "read" ? ["GET", "HEAD", "OPTIONS"] : var.access_type == "read_write" ? ["GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"] : ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
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

variable "s3_log_bucket_name" {
  type = string
}

variable "default_page_file" {
  type = string
  default = null
}

variable "status_404_page_file" {
  type = string
  default = null
}

variable "status_500_page_file" {
  type = string
  default = null
}

variable "bucket_name" {}

variable "origin_access_identity_path" {}

variable "price_class" {
  type = string
  default = "PriceClass_200"
}

variable "access_type" {
  type = string
}

variable "acm_cert_arn" {
  type = string
  default = null
}

variable "domains" {
  type = list(string)
  default = []
}

variable "links" {
  default = []
}