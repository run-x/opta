resource "aws_docdb_subnet_group" "main" {
  name       = "opta-${var.layer_name}-docdb"
  subnet_ids = local.private_subnet_ids
  tags = {
    "purpose" : "docdb"
    "ignore-if-seemingly-out-of-place" : "yup"
  }
}
