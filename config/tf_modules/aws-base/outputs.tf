output "kms_account_key_arn" {
  value = aws_kms_key.key.arn
}

output "s3_log_bucket_name" {
  value = aws_s3_bucket.log_bucket.id
}

output "kms_account_key_id" {
  value = aws_kms_key.key.id
}

output "vpc_id" {
  value = aws_vpc.vpc.id
}

output "private_subnet_ids" {
  value = aws_subnet.private_subnets.*.id
}

output "public_subnets_ids" {
  value = aws_subnet.public_subnets.*.id
}
