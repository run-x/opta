resource "aws_subnet" "public_subnets" {
  count                   = local.create_vpc ? length(var.public_ipv4_cidr_blocks) : 0
  cidr_block              = var.public_ipv4_cidr_blocks[count.index]
  availability_zone_id    = data.aws_availability_zones.current.zone_ids[count.index]
  vpc_id                  = local.vpc_id
  map_public_ip_on_launch = true

  tags = {
    Name                                           = "opta-${var.layer_name}-public-${data.aws_availability_zones.current.zone_ids[count.index]}"
    "kubernetes.io/cluster/opta-${var.layer_name}" = "shared"
    type                                           = "public"
    terraform                                      = "true"
    "kubernetes.io/role/elb"                       = "1"
  }
}

resource "aws_route_table" "public_route_table" {
  count  = local.create_vpc ? 1 : 0
  vpc_id = local.vpc_id
  tags = {
    Name      = "opta-${var.layer_name}-public"
    terraform = "true"
  }
}

resource "aws_internet_gateway" "igw" {
  count = local.create_vpc ? 1 : 0

  vpc_id = local.vpc_id

  tags = {
    Name      = "opta-${var.layer_name}-internet-gateway"
    terraform = "true"
  }
}

resource "aws_route" "igw_routes" {
  count                  = local.create_vpc ? length(var.public_ipv4_cidr_blocks) : 0
  route_table_id         = aws_route_table.public_route_table[0].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw[0].id
}

resource "aws_route_table_association" "public_association" {
  count          = local.create_vpc ? length(var.public_ipv4_cidr_blocks) : 0
  route_table_id = aws_route_table.public_route_table[0].id
  subnet_id      = aws_subnet.public_subnets[count.index].id
}
