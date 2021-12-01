resource "aws_elasticache_subnet_group" "main" {
  name       = "opta-${var.layer_name}"
  subnet_ids = aws_subnet.private_subnets[*].id
}
