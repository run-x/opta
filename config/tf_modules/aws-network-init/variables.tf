data aws_region "current" {}
data aws_availability_zones "current" {}

variable "name" {
  description = "Name to be given to vpc"
  type        = string
}

variable "total_ipv4_cidr_block" {
  description = "Cidr block to reserve for whole vpc"
  type        = string
}

variable "private_ipv4_cidr_blocks" {
  description = "Cidr blocks for private subnets. One for each desired AZ"
  type        = list(string)
  default     = []
}

variable "public_ipv4_cidr_blocks" {
  description = "Cidr blocks for public subnets. One for each desired AZ"
  type        = list(string)
  default     = []
}

variable "subnet_tags" {
  type    = map(string)
  default = {}
}
