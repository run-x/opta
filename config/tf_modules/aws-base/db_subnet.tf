resource "aws_db_subnet_group" "main" {
  name       = "opta-${var.layer_name}"
  subnet_ids = aws_subnet.private_subnets[*].id
  tags = {
    "purpose": "postgres"
    "ignore-if-seemingly-out-of-place": "yup"
  }
}