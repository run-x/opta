data "aws_vpc" "vpc" {
  count = local.create_vpc ? 0 : 1
  id    = var.vpc_id
  state = "available"
}

data "aws_subnet" "public_subnets" {
  for_each = local.create_vpc ? toset([]) : toset(var.public_subnet_ids)
  id       = each.key
  vpc_id   = var.vpc_id
  state    = "available"
}

data "aws_subnet" "private_subnets" {
  for_each = local.create_vpc ? toset([]) : toset(var.private_subnet_ids)
  id       = each.key
  vpc_id   = var.vpc_id
  state    = "available"
}

data "aws_nat_gateway" "nat_gateways" {
  for_each = data.aws_route.private_nat_routes
  id       = each.value.nat_gateway_id
  state    = "available"
}

data "aws_route_table" "private_subnet_routes" {
  for_each  = data.aws_subnet.private_subnets
  subnet_id = each.value.id
  vpc_id    = var.vpc_id
}

data "aws_route" "private_nat_routes" {
  for_each               = data.aws_route_table.private_subnet_routes
  route_table_id         = each.value.id
  destination_cidr_block = "0.0.0.0/0"
}
