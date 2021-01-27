variable "openid_provider_url" {
  type = string
}

variable "openid_provider_arn" {
  type = string
}

variable "zone_type" {
  type = string
  default = "public"
}

variable "hosted_zone_id" {
  type = string
}

variable "domain" {
  type = string
}