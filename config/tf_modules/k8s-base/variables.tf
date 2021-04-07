locals {
  target_ports = var.cert_arn == "" ? { http: "http" } : { http: "http", https: "special" }
  container_ports = var.cert_arn == "" ? { http: 80, https: 443 } : { http: 80, https: 443, special: 8000 }
  config = var.cert_arn == "" ? { ssl-redirect: false } : {
    ssl-redirect: false
    server-snippet: <<EOF
          listen 8000;
          if ( $server_port = 80 ) {
             return 308 https://$host$request_uri;
          }
          EOF
  }
}

data "aws_region" "current" {}

data "aws_eks_cluster" "main" {
  name = "opta-${var.env_name}"
}

variable "env_name" {
  description = "Env name"
  type = string
}

variable "layer_name" {
  description = "Layer name"
  type        = string
}

variable "module_name" {
  description = "Module name"
  type = string
}

variable "domain" {
  type = string
  default = ""
}

variable "cert_arn" {
  type = string
  default = ""
}

variable "openid_provider_url" {
  type = string
}

variable "openid_provider_arn" {
  type = string
}

variable "high_availability" {
  type = bool
  default = true
}

data "aws_vpc" "main" {
  tags = {
    Name = "opta-${var.env_name}"
  }
}

data "aws_subnet_ids" "public" {
  vpc_id = data.aws_vpc.main.id
  tags = {
    type = "public"
  }
}
