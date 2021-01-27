resource "aws_subnet" "private_subnets" {
  count                = length(var.private_ipv4_cidr_blocks)
  cidr_block           = var.private_ipv4_cidr_blocks[count.index]
  availability_zone_id = data.aws_availability_zones.current.zone_ids[count.index]
  vpc_id               = aws_vpc.vpc.id

  tags = merge({
    Name      = "${var.name}-private-${data.aws_availability_zones.current.zone_ids[count.index]}"
    terraform = "true"
  }, var.subnet_tags)
}

resource "aws_route_table" "private_route_tables" {
  count  = length(var.private_ipv4_cidr_blocks)
  vpc_id = aws_vpc.vpc.id
  tags = {
    Name      = "${var.name}-private-${data.aws_availability_zones.current.zone_ids[count.index]}"
    terraform = "true"
  }
}

resource "aws_route_table_association" "private_associations" {
  count          = length(var.private_ipv4_cidr_blocks)
  route_table_id = aws_route_table.private_route_tables[count.index].id
  subnet_id      = aws_subnet.private_subnets[count.index].id
}

resource "aws_eip" "nat_eips" {
  count = length(var.private_ipv4_cidr_blocks)
  vpc   = true
  tags = {
    Name      = "${var.name}-nat-ip-${data.aws_availability_zones.current.zone_ids[count.index]}"
    terraform = "true"
  }
}

resource "aws_nat_gateway" "nat_gateways" {
  count         = length(var.private_ipv4_cidr_blocks)
  allocation_id = aws_eip.nat_eips[count.index].id
  subnet_id     = aws_subnet.public_subnets[count.index].id
  tags = {
    terraform = "true"
  }
}

resource "aws_route" "nat_routes" {
  count                  = length(var.private_ipv4_cidr_blocks)
  route_table_id         = aws_route_table.private_route_tables[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.nat_gateways[count.index].id
}