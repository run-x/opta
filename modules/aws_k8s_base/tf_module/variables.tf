data "aws_region" "current" {}
data "aws_eks_cluster" "current" {
  name = var.k8s_cluster_name
}

locals {
  target_ports    = var.cert_arn == "" && var.private_key == "" && !var.expose_self_signed_ssl ? { http : "http" } : { http : "http", https : "https" }
  container_ports = { http : 80, https : 443, healthcheck : 10254 }
  nginx_tls_ports = var.cert_arn == "" && var.private_key == "" && !var.expose_self_signed_ssl ? "" : join(",", compact(flatten([
    ["https"],
    [for port in var.nginx_extra_tcp_ports_tls : "${port}-tcp"],
  ])))

  config = merge((var.cert_arn == "" && var.private_key == "" ? { ssl-redirect : false } : {
    ssl-redirect : true
    force-ssl-redirect : true
  }), var.nginx_config)
  load_balancer_name = "opta-${substr(var.layer_name, 0, 22)}-lb"
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
  type = string
  # Ignore since this default value is never used, its for a logical if condition checking if user specified no private_key only.
  #tfsec:ignore:general-secrets-no-plaintext-exposure
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

variable "enable_auto_dns" {
  type = bool
}

variable "domain" {
  type = string
}

variable "zone_id" {
  type = string
}

variable "nginx_enabled" {
  type = bool
}