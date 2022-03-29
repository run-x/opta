resource "random_id" "bucket_suffix" {
  byte_length = 8
}

# Changes based on the AWS terraform provider upgrade from 3.70.0 to 4.3.0

resource "aws_s3_bucket" "log_bucket" {
  bucket        = "opta-${var.env_name}-logging-bucket-${random_id.bucket_suffix.hex}"
  force_destroy = true

  lifecycle {
    ignore_changes = [bucket]
  }
}

resource "aws_s3_bucket_public_access_block" "log_bucket" {
  bucket = aws_s3_bucket.log_bucket.id

  block_public_acls   = true
  block_public_policy = true
  restrict_public_buckets = true
  ignore_public_acls = true

}

resource "aws_s3_bucket_acl" "log_bucket" {
  bucket = aws_s3_bucket.log_bucket.id
  acl    = "log-delivery-write"
}

resource "aws_s3_bucket_versioning" "log_bucket" {
  bucket = aws_s3_bucket.log_bucket.id
  versioning_configuration {
    status = "Enabled"
  }
}

# Opta makes a design choice and uses public cloud provider managed encryption keys
# They are very well administered by the cloud providers, and save the user from
# a lot of key management overhead.
#tfsec:ignore:aws-s3-encryption-customer-key
resource "aws_s3_bucket_server_side_encryption_configuration" "log_bucket" {
  bucket = aws_s3_bucket.log_bucket.id
  rule {
    bucket_key_enabled = false
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "log_bucket" {
  bucket = aws_s3_bucket.log_bucket.id

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
      noncurrent_days = 90
    }
  }

  depends_on = [aws_s3_bucket_versioning.log_bucket]
}

# Visit (https://run-x.atlassian.net/browse/RUNX-1125) for further reference

data "aws_iam_policy_document" "log_bucket_policy" {
  statement {
    sid = "AWSLogDeliveryWrite"

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    effect = "Allow"

    actions = [
      "s3:PutObject",
    ]

    resources = [
      "${aws_s3_bucket.log_bucket.arn}/*",
    ]

    condition {
      test     = "StringEquals"
      variable = "s3:x-amz-acl"
      values   = ["bucket-owner-full-control"]
    }
  }

  statement {
    sid = "AWSLogDeliveryAclCheck"

    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["delivery.logs.amazonaws.com"]
    }

    actions = [
      "s3:GetBucketAcl",
    ]

    resources = [
      aws_s3_bucket.log_bucket.arn,
    ]

  }

  statement {
    sid    = "denyInsecureTransport"
    effect = "Deny"

    actions = [
      "s3:*",
    ]

    resources = [
      aws_s3_bucket.log_bucket.arn,
      "${aws_s3_bucket.log_bucket.arn}/*",
    ]

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values = [
        "false"
      ]
    }
  }
}

resource "aws_s3_bucket_policy" "log_bucket_policy" {
  bucket = aws_s3_bucket.log_bucket.id
  policy = data.aws_iam_policy_document.log_bucket_policy.json
  # Visit (https://run-x.atlassian.net/browse/RUNX-1125) for further reference
}