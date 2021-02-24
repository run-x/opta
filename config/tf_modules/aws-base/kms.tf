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
    sid    = "Allow service-linked role use of the CMK"
    effect = "Allow"
    principals {
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling"]
      type        = "AWS"
    }
    actions = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey"
    ]
    resources = ["*"]
  }

  statement {
    sid    = "Allow attachment of persistent resources"
    effect = "Allow"
    principals {
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/aws-service-role/autoscaling.amazonaws.com/AWSServiceRoleForAutoScaling"]
      type        = "AWS"
    }
    actions = [
      "kms:CreateGrant",
      "kms:ListGrants",
      "kms:RevokeGrant"
    ]
    resources = ["*"]
    condition {
      test     = "Bool"
      values   = [true]
      variable = "kms:GrantIsForAWSResource"
    }
  }
}

resource "aws_kms_key" "key" {
  description = "Base key for account"
  policy      = data.aws_iam_policy_document.kms_policy.json
  tags = {
    Name = "opta-${var.layer_name}"
    terraform = "true"
  }
}

resource "aws_kms_alias" "alias" {
  name          = "alias/opta-${var.layer_name}"
  target_key_id = aws_kms_key.key.key_id
}