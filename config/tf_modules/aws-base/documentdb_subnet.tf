resource "aws_docdb_subnet_group" "main" {
  name       = "opta-${var.layer_name}-docdb"
  subnet_ids = aws_subnet.private_subnets[*].id
  tags = {
    "purpose" : "docdb"
    "ignore-if-seemingly-out-of-place" : "yup"
  }
}