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

variable "private_key_file" {
  type = string
  # Ignore since this default value is never used, its for a logical if condition checking if user specified no private_key_file.
  #tfsec:ignore:general-secrets-no-plaintext-exposure
  default = ""
}

variable "certificate_body_file" {
  type    = string
  default = ""
}

variable "certificate_chain_file" {
  type    = string
  default = ""
}

variable "private_key" {
  type = string
}

variable "certificate_body" {
  type = string
}

variable "certificate_chain" {
  type = string
}

variable "domain" {
  type = string
}
