locals {
  create_vpc         = var.vpc_id == null
  vpc_id             = local.create_vpc ? aws_vpc.vpc[0].id : data.aws_vpc.vpc[0].id
  vpc_cidr_blocks    = local.create_vpc ? [aws_vpc.vpc[0].cidr_block] : data.aws_vpc.vpc[0].cidr_block_associations[*].cidr_block
  private_subnet_ids = local.create_vpc ? aws_subnet.private_subnets[*].id : values(data.aws_subnet.private_subnets)[*].id
  public_subnet_ids  = local.create_vpc ? aws_subnet.public_subnets[*].id : values(data.aws_subnet.public_subnets)[*].id
  public_nat_ips     = local.create_vpc ? aws_eip.nat_eips[*].public_ip : values(data.aws_nat_gateway.nat_gateways)[*].public_ip
}
