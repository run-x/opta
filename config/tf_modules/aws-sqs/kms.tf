# Based off the following documents:
# https://docs.aws.amazon.com/kms/latest/developerguide/key-policies.html#key-policy-example
# https://docs.aws.amazon.com/autoscaling/ec2/userguide/key-policy-requirements-EBS-encryption.html
data "aws_iam_policy_document" "kms_policy" {
  statement {
    sid    = "Enable IAM User/Role Permissions"
    effect = "Allow"
    principals {
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
      type        = "AWS"
    }
    actions   = ["kms:*"]
    resources = ["*"]
  }

  statement {
    sid    = "Allow sns access"
    effect = "Allow"
    principals {
      identifiers = ["sns.amazonaws.com"]
      type        = "Service"
    }
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "Allow events access"
    effect = "Allow"
    principals {
      identifiers = ["events.amazonaws.com"]
      type        = "Service"
    }
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "Allow s3 access"
    effect = "Allow"
    principals {
      identifiers = ["s3.amazonaws.com"]
      type        = "Service"
    }
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKey*"
    ]
    resources = ["*"]
  }
}

resource "aws_kms_key" "key" {
  description         = "SQS Key"
  policy              = data.aws_iam_policy_document.kms_policy.json
  enable_key_rotation = true
  tags = {
    Name      = "opta-${var.layer_name}"
    terraform = "true"
  }
}
