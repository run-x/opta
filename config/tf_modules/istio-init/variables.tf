variable "domain_names" {
  type = list(string)
  default = []
}

variable "acm_cert_arn" {
  type = string
  default = ""
}