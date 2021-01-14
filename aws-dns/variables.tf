variable "domain_name" {
  type = string
}

variable "is_private" {
  type = bool
  default = false
}

variable "vpc_id" {
  type = string
  default = ""
}