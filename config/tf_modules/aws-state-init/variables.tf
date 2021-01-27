data "aws_caller_identity" "current" {}

variable "bucket_name" {
  type = string
}

variable "dynamodb_lock_table_name" {
  type = string
}