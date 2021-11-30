# Based off https://docs.aws.amazon.com/kms/latest/developerguide/services-dynamodb.html
data "aws_iam_policy_document" "kms_policy" {
  statement {
    sid    = "Allow access through Amazon DynamoDB for all principals in the account that are authorized to use Amazon DynamoDB"
    effect = "Allow"
    principals {
      identifiers = ["*"]
      type        = "AWS"
    }
    actions   = ["kms:Describe*", "kms:Get*", "kms:List*", "kms:RevokeGrant"]
    resources = ["*"]
    condition {
      test     = "StringEquals"
      values   = ["${data.aws_caller_identity.current.account_id}"]
      variable = "kms:CallerAccount"
    }
    condition {
      test     = "StringEquals"
      values   = ["dynamodb.${data.aws_region.current.name}.amazonaws.com"]
      variable = "kms:ViaService"
    }
  }

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
}

resource "aws_kms_key" "key" {
  description         = "DynamoDB Key"
  policy              = data.aws_iam_policy_document.kms_policy.json
  enable_key_rotation = true
  tags = {
    Name      = "opta-${var.layer_name}"
    terraform = "true"
  }
}
