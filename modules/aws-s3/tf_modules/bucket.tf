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

  versioning {
    enabled = true
  }
  dynamic "logging" {
    for_each = var.s3_log_bucket_name == null ? [] : [1]
    content {
      target_bucket = var.s3_log_bucket_name
      target_prefix = "log/"
    }
  }

  lifecycle_rule {
    enabled = true

    noncurrent_version_transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    noncurrent_version_transition {
      days          = 60
      storage_class = "GLACIER"
    }

    noncurrent_version_expiration {
      days = 90
    }
  }

  dynamic "cors_rule" {
    for_each = var.cors_rule != null ? [var.cors_rule] : []
    content {
      allowed_headers = try(cors_rule.value["allowed_headers"], [])
      allowed_methods = try(cors_rule.value["allowed_methods"], [])
      allowed_origins = try(cors_rule.value["allowed_origins"], [])
      expose_headers  = try(cors_rule.value["expose_headers"], [])
      max_age_seconds = try(cors_rule.value["max_age_seconds"], 0)
    }
  }

  dynamic "replication_configuration" {
    for_each = var.same_region_replication ? [1] : []
    content {
      role = aws_iam_role.replication[0].arn
      rules {
        id     = "default"
        status = "Enabled"

        destination {
          bucket        = aws_s3_bucket.replica[0].arn
          storage_class = "STANDARD"
        }
      }
    }
  }
}

# It's fine adding this as it's just creating something akin to an IAM role.
resource "aws_cloudfront_origin_access_identity" "read" {
  comment = "For reading bucket ${var.bucket_name}"
}


data "aws_iam_policy_document" "s3_policy" {
  source_json = var.bucket_policy == null ? "" : var.bucket_policy
  statement {
    sid       = "Cloudfront Reading"
    actions   = ["s3:ListBucket", "s3:GetObject"]
    resources = [aws_s3_bucket.bucket.arn, "${aws_s3_bucket.bucket.arn}/*"]

    principals {
      type = "AWS"
      identifiers = [
        aws_cloudfront_origin_access_identity.read.iam_arn,
      ]
    }
  }
}

resource "aws_s3_bucket_public_access_block" "block" {
  count  = var.block_public ? 1 : 0
  bucket = aws_s3_bucket.bucket.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_policy" "policy" {
  bucket = aws_s3_bucket.bucket.id
  policy = data.aws_iam_policy_document.s3_policy.json
}
