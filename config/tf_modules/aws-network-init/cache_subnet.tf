resource "aws_elasticache_subnet_group" "main" {
  name       = "main"
  subnet_ids = aws_subnet.private_subnets[*].id
}