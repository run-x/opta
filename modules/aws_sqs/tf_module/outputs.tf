output "queue_arn" {
  value = aws_sqs_queue.terraform_queue.arn
}

output "queue_id" {
  value = aws_sqs_queue.terraform_queue.id
}

output "queue_name" {
  value = aws_sqs_queue.terraform_queue.name
}

output "kms_arn" {
  value = aws_kms_key.key.arn
}
