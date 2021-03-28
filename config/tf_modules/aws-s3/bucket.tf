resource "aws_s3_bucket" "bucket" {
  bucket = var.bucket_name
  server_side_encryption_configuration {
    rule {
      apply_server_side_encryption_by_default {
        sse_algorithm = "AES256"
      }
    }
  }
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "block" {
  count = var.block_public? 1 : 0
  bucket = aws_s3_bucket.bucket.id

  block_public_acls   = true
  block_public_policy = true
  ignore_public_acls = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "policy" {
  count = var.bucket_policy == null ? 0 : 1
  bucket = aws_s3_bucket.bucket.id
  policy = var.bucket_policy == null? null : jsonencode(var.bucket_policy)
}
