resource "aws_db_subnet_group" "main" {
  name       = "opta-${var.layer_name}"
  subnet_ids = local.private_subnet_ids
  tags = {
    "purpose" : "postgres"
    "ignore-if-seemingly-out-of-place" : "yup"
  }
}
