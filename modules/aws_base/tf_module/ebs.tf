resource "aws_ebs_default_kms_key" "default" {
  key_arn = aws_kms_key.key.arn
}

resource "aws_ebs_encryption_by_default" "default" {
  enabled = true
}