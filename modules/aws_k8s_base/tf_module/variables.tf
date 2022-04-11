data "aws_region" "current" {}
data "aws_eks_cluster" "current" {
  name = var.k8s_cluster_name
}

locals {
  target_ports    = var.cert_arn == "" && var.private_key == "" && !var.expose_self_signed_ssl ? { http : "http" } : { http : "http", https : "https" }
  container_ports = { http : 80, https : 443, healthcheck : 10254 }
  nginx_tls_ports = var.cert_arn == "" && var.private_key == "" ? "" : join(",", compact(flatten([
    ["https"],
    [for port in var.nginx_extra_tcp_ports_tls : "${port}-tcp"],
  ])))

  config = merge((var.cert_arn == "" && var.private_key == "" && !var.expose_self_signed_ssl ? { ssl-redirect : false } : {
    ssl-redirect : true
    force-ssl-redirect : true
  }), var.nginx_config)
}

variable "eks_cluster_name" {
  type = string
}

variable "s3_log_bucket_name" {
  type = string
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

variable "domain" {
  type    = string
  default = ""
}

variable "cert_arn" {
  type    = string
  default = ""
}

variable "k8s_cluster_name" {
  type = string
}

variable "k8s_version" {
  type = string
}

variable "openid_provider_url" {
  type = string
}

variable "openid_provider_arn" {
  type = string
}

variable "nginx_high_availability" {
  type    = bool
  default = false
}

variable "linkerd_enabled" {
  type    = bool
  default = true
}

variable "linkerd_high_availability" {
  type    = bool
  default = false
}

variable "admin_arns" {
  type    = list(string)
  default = []
}

variable "private_key" {
  type    = string
  default = ""
}

variable "certificate_body" {
  type    = string
  default = ""
}

variable "certificate_chain" {
  type    = string
  default = ""
}

variable "nginx_config" {
  default = {}
}

variable "nginx_extra_tcp_ports" {
  type    = map(string)
  default = {}
}

variable "nginx_extra_tcp_ports_tls" {
  type    = list(number)
  default = []
}

variable "expose_self_signed_ssl" {
  type    = bool
  default = false
}

variable "cert_manager_values" {
  default = {}
}

variable "linkerd_values" {
  default = {}
}

variable "ingress_nginx_values" {
  default = {}
}