data "aws_iam_policy_document" "replication_trust" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      identifiers = ["s3.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "replication" {
  count = var.same_region_replication ? 1 : 0
  name  = "opta-${var.layer_name}-${var.module_name}-replication"

  assume_role_policy = data.aws_iam_policy_document.replication_trust.json
}


data "aws_iam_policy_document" "replication" {
  statement {
    actions = [
      "s3:GetReplicationConfiguration",
      "s3:ListBucket"
    ]
    resources = ["${aws_s3_bucket.bucket.arn}"]
    sid       = "ReadSourceBucket"
  }

  statement {
    actions = ["s3:GetObjectVersionForReplication",
      "s3:GetObjectVersionAcl",
    "s3:GetObjectVersionTagging"]
    resources = ["${aws_s3_bucket.bucket.arn}/*"]
    sid       = "ReadSourceBucketInside"
  }

  statement {
    actions = [
      "s3:ReplicateObject",
      "s3:ReplicateDelete",
      "s3:ReplicateTags"
    ]
    resources = ["${aws_s3_bucket.replica[0].arn}/*"]
    sid       = "DoReplication"
  }
}


resource "aws_iam_policy" "replication" {
  count = var.same_region_replication ? 1 : 0
  name  = "opta-${var.layer_name}-${var.module_name}-replication"

  policy = data.aws_iam_policy_document.replication.json
}

resource "aws_iam_role_policy_attachment" "replication" {
  count      = var.same_region_replication ? 1 : 0
  role       = aws_iam_role.replication[0].name
  policy_arn = aws_iam_policy.replication[0].arn
}

resource "aws_s3_bucket" "replica" {
  count  = var.same_region_replication ? 1 : 0
  bucket = "${var.bucket_name}-replica"

  versioning {
    enabled = true
  }

  logging {
    target_bucket = var.s3_log_bucket_name
    target_prefix = "log/"
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
}

resource "aws_s3_bucket_public_access_block" "block_for_replica" {
  count  = var.same_region_replication ? 1 : 0
  bucket = aws_s3_bucket.replica[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}


data "aws_iam_policy_document" "replica_bucket_policy" {
  statement {
    sid    = "denyInsecureTransport"
    effect = "Deny"

    actions = [
      "s3:*",
    ]

    resources = [
      aws_s3_bucket.replica[0].arn,
      "${aws_s3_bucket.replica[0].arn}/*",
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

resource "aws_s3_bucket_policy" "replica_bucket_policy" {
  count  = var.same_region_replication ? 1 : 0
  bucket = aws_s3_bucket.replica[0].id
  policy = data.aws_iam_policy_document.replica_bucket_policy.json
  depends_on = [
    aws_s3_bucket_public_access_block.block[0]
  ]
}