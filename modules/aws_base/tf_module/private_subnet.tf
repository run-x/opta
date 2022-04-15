resource "aws_subnet" "private_subnets" {
  count                = local.create_vpc ? length(var.private_ipv4_cidr_blocks) : 0
  cidr_block           = var.private_ipv4_cidr_blocks[count.index]
  availability_zone_id = data.aws_availability_zones.current.zone_ids[count.index]
  vpc_id               = local.vpc_id

  tags = {
    Name                                           = "opta-${var.layer_name}-private-${data.aws_availability_zones.current.zone_ids[count.index]}"
    "kubernetes.io/cluster/opta-${var.layer_name}" = "shared"
    type                                           = "private"
    terraform                                      = "true"
    "kubernetes.io/role/internal-elb"              = "1"
  }
}

resource "aws_route_table" "private_route_tables" {
  count  = local.create_vpc ? length(var.private_ipv4_cidr_blocks) : 0
  vpc_id = local.vpc_id
  tags = {
    Name      = "opta-${var.layer_name}-private-${data.aws_availability_zones.current.zone_ids[count.index]}"
    terraform = "true"
  }
}

resource "aws_route_table_association" "private_associations" {
  count          = local.create_vpc ? length(var.private_ipv4_cidr_blocks) : 0
  route_table_id = aws_route_table.private_route_tables[count.index].id
  subnet_id      = aws_subnet.private_subnets[count.index].id
}

resource "aws_eip" "nat_eips" {
  count = local.create_vpc ? length(var.private_ipv4_cidr_blocks) : 0
  vpc   = true
  tags = {
    Name      = "opta-${var.layer_name}-nat-ip-${data.aws_availability_zones.current.zone_ids[count.index]}"
    terraform = "true"
  }
}

resource "aws_nat_gateway" "nat_gateways" {
  count         = local.create_vpc ? length(var.private_ipv4_cidr_blocks) : 0
  allocation_id = aws_eip.nat_eips[count.index].id
  subnet_id     = aws_subnet.public_subnets[count.index].id
  tags = {
    Name      = "opta-${var.layer_name}-${data.aws_availability_zones.current.zone_ids[count.index]}"
    terraform = "true"
  }
}

resource "aws_route" "nat_routes" {
  count                  = local.create_vpc ? length(var.private_ipv4_cidr_blocks) : 0
  route_table_id         = aws_route_table.private_route_tables[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat_gateways[count.index].id
}
