output "vpc_id" {
  value = aws_vpc.vpc.id
}

output "private_subnet_ids" {
  value = aws_subnet.private_subnets.*.id
}

output "public_subnets_ids" {
  value = aws_subnet.public_subnets.*.id
}

output "db_subnet_group_name" {
  value = aws_db_subnet_group.main.name
}
