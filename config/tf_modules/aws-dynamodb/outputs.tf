output "table_arn" {
  value = var.range_key == null ? aws_dynamodb_table.table_no_range[0].arn : aws_dynamodb_table.table_with_range[0].arn
}

output "table_id" {
  value = var.range_key == null ? aws_dynamodb_table.table_no_range[0].id : aws_dynamodb_table.table_with_range[0].id
}

output "kms_arn" {
  value = aws_kms_key.key.arn
}

output "kms_id" {
  value = aws_kms_key.key.id
}
