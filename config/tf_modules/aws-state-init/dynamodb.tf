resource "aws_dynamodb_table" "tfstate" {
  hash_key = "LockID"
  name = var.dynamodb_lock_table_name
  write_capacity = 20
  read_capacity = 20
  attribute {
    name = "LockID"
    type = "S"
  }
}