output "state_bucket_id" {
  value = aws_s3_bucket.tf-state-bucket.id
}

output "state_bucket_arn" {
  value = aws_s3_bucket.tf-state-bucket.arn
}

output "kms_account_key_arn" {
  value = aws_kms_key.key.arn
}

output "kms_account_key_id" {
  value = aws_kms_key.key.id
}
