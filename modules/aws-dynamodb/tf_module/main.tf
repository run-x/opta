resource "random_string" "db_name_hash" {
  length  = 4
  special = false
  upper   = false
}

resource "aws_dynamodb_table" "table_no_range" {
  count          = var.range_key == null ? 1 : 0
  hash_key       = var.hash_key
  name           = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  read_capacity  = var.read_capacity
  write_capacity = var.write_capacity
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.key.arn
  }
  point_in_time_recovery {
    enabled = true
  }
  dynamic "attribute" {
    for_each = var.attributes
    content {
      name = attribute.value["name"]
      type = attribute.value["type"]
    }
  }
}

resource "aws_dynamodb_table" "table_with_range" {
  count          = var.range_key == null ? 0 : 1
  hash_key       = var.hash_key
  range_key      = var.range_key
  name           = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  read_capacity  = var.read_capacity
  write_capacity = var.write_capacity
  server_side_encryption {
    enabled     = true
    kms_key_arn = aws_kms_key.key.arn
  }
  point_in_time_recovery {
    enabled = true
  }
  dynamic "attribute" {
    for_each = var.attributes
    content {
      name = attribute.value["name"]
      type = attribute.value["type"]
    }
  }
}