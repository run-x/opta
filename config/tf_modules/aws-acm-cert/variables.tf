variable "primary_domain" {
  description = "Primary domain for the certs"
  type        = string
}

variable "secondary_domains" {
  description = "Secondary domains to add to the cert"
  default     = []
  type        = list(string)
}

variable "hosted_zone_id" {
  description = "Hosted zone to make verfications for"
  type        = string
}
