data "aws_iam_policy_document" "k8s_service" {
  statement {
    actions = [
      "eks:DescribeCluster"
    ]
    resources = ["*"]
    sid = "describeCluster"
  }

  dynamic "statement" {
    for_each = length(var.read_buckets) == 1 ? ["allow_read"] : []
    content {
      sid = "ReadBuckets"
      actions = [
        "s3:GetObject*",
        "s3:ListBucket",
      ]
      resources = concat(formatlist("arn:aws:s3:::%s", var.read_buckets), formatlist("arn:aws:s3:::%s/*", var.read_buckets))
    }
  }

  dynamic "statement" {
    for_each = length(var.write_buckets) == 1 ? ["allow_write"] : []
    content {
      sid = "WriteBuckets"
      actions = [
        "s3:GetObject*",
        "s3:PutObject*",
        "s3:DeleteObject*",
        "s3:ListBucket",
      ]
      resources = concat(formatlist("arn:aws:s3:::%s", var.write_buckets), formatlist("arn:aws:s3:::%s/*", var.write_buckets))
    }
  }
}

resource "aws_iam_policy" "k8s_service" {
  name = "${var.layer_name}-${var.module_name}"
  policy = data.aws_iam_policy_document.k8s_service.json
}

data "aws_iam_policy_document" "trust_k8s_openid" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.k8s_openid_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.layer_name}:${var.module_name}"]
    }

    principals {
      identifiers = [var.k8s_openid_provider_arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "k8s_service" {
  assume_role_policy = data.aws_iam_policy_document.trust_k8s_openid.json
  name = "${var.layer_name}-${var.module_name}"
}

resource "aws_iam_policy_attachment" "k8s_service" {
  name = "${var.layer_name}-${var.module_name}"
  policy_arn = aws_iam_policy.k8s_service.arn
  roles = [aws_iam_role.k8s_service.name]
}