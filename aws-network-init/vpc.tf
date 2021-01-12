resource "aws_vpc" "vpc" {
  cidr_block           = var.total_ipv4_cidr_block
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name      = var.name
    terraform = "true"
  }
}
