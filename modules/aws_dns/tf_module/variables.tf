variable "domain" {
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

variable "delegated" {
  type    = bool
  default = false
}

variable "upload_cert" {
  type    = bool
  default = false
}

variable "cert_chain_included" {
  type    = bool
  default = false
}

variable "force_update" {
  type    = bool
  default = false
}

variable "external_cert_arn" {
  type    = string
  default = ""
}

variable "linked_module" {
  type = string
}

data "aws_ssm_parameter" "private_key" {
  count           = var.upload_cert ? 1 : 0
  name            = "/opta-${var.env_name}/dns-private-key.pem"
  with_decryption = true
}

data "aws_ssm_parameter" "certificate_body" {
  count           = var.upload_cert ? 1 : 0
  name            = "/opta-${var.env_name}/dns-certificate-body.pem"
  with_decryption = true
}

data "aws_ssm_parameter" "certificate_chain" {
  count           = var.cert_chain_included ? 1 : 0
  name            = "/opta-${var.env_name}/dns-certificate-chain.pem"
  with_decryption = true
}
