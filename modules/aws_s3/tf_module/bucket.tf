resource "aws_s3_bucket" "bucket" {
  bucket        = var.bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "bucket" {
  bucket = aws_s3_bucket.bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "bucket" {
  bucket = aws_s3_bucket.bucket.id

  rule {
    id     = "log_bucket_lifecycle_configuration"
    status = "Enabled"

    noncurrent_version_transition {
      newer_noncurrent_versions = null
      noncurrent_days           = 30
      storage_class             = "STANDARD_IA"
    }

    noncurrent_version_transition {
      newer_noncurrent_versions = null
      noncurrent_days           = 60
      storage_class             = "GLACIER"
    }

    noncurrent_version_expiration {
      newer_noncurrent_versions = null
      noncurrent_days           = 90
    }
  }

  depends_on = [aws_s3_bucket_versioning.bucket]
}

resource "aws_s3_bucket_replication_configuration" "bucket" {
  count      = var.same_region_replication ? 1 : 0
  depends_on = [aws_s3_bucket_versioning.bucket]

  role   = aws_iam_role.replication[0].arn
  bucket = aws_s3_bucket.bucket.id

  rule {
    id     = "default"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.replica[0].arn
      storage_class = "STANDARD"
    }
  }
}

resource "aws_s3_bucket_cors_configuration" "bucket" {
  bucket = aws_s3_bucket.bucket.id
  count  = var.cors_rule != null ? 1 : 0

  cors_rule {
    allowed_headers = try(var.cors_rule["allowed_headers"], [])
    allowed_methods = try(var.cors_rule["allowed_methods"], [])
    allowed_origins = try(var.cors_rule["allowed_origins"], [])
    expose_headers  = try(var.cors_rule["expose_headers"], [])
    max_age_seconds = try(var.cors_rule["max_age_seconds"], 0)
  }
}

#Ignore this because in Opta we made a user-friendly
#choice of automatic cloud-provider key management
#tfsec:ignore:aws-s3-encryption-customer-key
resource "aws_s3_bucket_server_side_encryption_configuration" "bucket" {
  bucket = aws_s3_bucket.bucket.id
  rule {
    bucket_key_enabled = false
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_logging" "bucket" {
  count  = var.s3_log_bucket_name == null ? 0 : 1
  bucket = aws_s3_bucket.bucket.id

  target_bucket = var.s3_log_bucket_name
  target_prefix = "log/"
}

# It's fine adding this as it's just creating something akin to an IAM role.
resource "aws_cloudfront_origin_access_identity" "read" {
  comment = "For reading bucket ${var.bucket_name}"
}


data "aws_iam_policy_document" "s3_policy" {
  source_policy_documents = var.bucket_policy == null ? [] : [jsonencode(var.bucket_policy)]
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
  depends_on              = [aws_s3_bucket_policy.policy]
}

resource "aws_s3_bucket_ownership_controls" "ownership_controls" {
  bucket = aws_s3_bucket.bucket.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_policy" "policy" {
  bucket = aws_s3_bucket.bucket.id
  policy = data.aws_iam_policy_document.s3_policy.json
}
