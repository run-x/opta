resource "aws_docdb_subnet_group" "main" {
  name       = "main-docdb"
  subnet_ids = aws_subnet.private_subnets[*].id
  tags = {
    "purpose": "docdb"
    "ignore-if-seemingly-out-of-place": "yup"
  }
}