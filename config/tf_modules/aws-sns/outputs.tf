output "topic_arn" {
  value = aws_sns_topic.topic.arn
}

output "kms_arn" {
  value = aws_kms_key.key.arn
}