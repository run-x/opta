output "kms_account_key_arn" {
  value = aws_kms_key.key.arn
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
