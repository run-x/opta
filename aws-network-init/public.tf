resource "aws_subnet" "public_subnets" {
  count                   = length(var.public_ipv4_cidr_blocks)
  cidr_block              = var.public_ipv4_cidr_blocks[count.index]
  availability_zone_id    = data.aws_availability_zones.current.zone_ids[count.index]
  vpc_id                  = aws_vpc.vpc.id
  map_public_ip_on_launch = true

  tags = merge({
    Name                         = "${var.name}-private-${data.aws_availability_zones.current.zone_ids[count.index]}"
    "kubernetes.io/cluster/main" = "shared"
    terraform                    = "true"
  }, var.subnet_tags)
}

resource "aws_route_table" "public_route_table" {
  vpc_id = aws_vpc.vpc.id
  tags = {
    Name      = "${var.name}-public"
    terraform = "true"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id

  tags = {
    Name      = "${var.name}-internet-gateway"
    terraform = "true"
  }
}

resource "aws_route" "igw_routes" {
  count                  = length(var.public_ipv4_cidr_blocks)
  route_table_id         = aws_route_table.public_route_table.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.igw.id
}

resource "aws_route_table_association" "public_association" {
  count          = length(var.public_ipv4_cidr_blocks)
  route_table_id = aws_route_table.public_route_table.id
  subnet_id      = aws_subnet.public_subnets[count.index].id
}