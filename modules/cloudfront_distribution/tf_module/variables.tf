locals {
  s3_origin_id = "optaDefaultOriginId"
  lb_origin_id = "optaDefaultLbOriginId"
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
}

variable "status_404_page_file" {
  type = string
}

variable "status_500_page_file" {
  type = string
}

variable "bucket_name" {}

variable "origin_access_identity_path" {}

variable "price_class" {
  type = string
}

variable "acm_cert_arn" {
  type = string
}

variable "domains" {
  type    = list(string)
  default = []
}

variable "links" {
  default = []
}

variable "load_balancer_arn" {
  type = string
}

variable "eks_load_balancer_enabled" {
  type = bool
}

variable "s3_load_balancer_enabled" {
  type = bool
}

variable "allowed_methods" {
  type    = list(string)
  default = ["GET", "HEAD", "OPTIONS"]
}

variable "cached_methods" {
  type    = list(string)
  default = ["GET", "HEAD", "OPTIONS"]
}

variable "enable_auto_dns" {
  type = bool
}

variable "zone_id" {
  type = string
}

variable "web_acl_id" {
  type = string
}

variable "extra_headers" {
  type = list(string)
}