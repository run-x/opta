resource "aws_iam_policy" "vanilla_policy" {
  name   = "${var.env_name}-${var.layer_name}-${var.module_name}"
  policy = jsonencode(var.iam_policy)
}

data "aws_iam_policy_document" "iam_trusts" {
  dynamic "statement" {
    for_each = var.kubernetes_trusts
    content {
      actions = ["sts:AssumeRoleWithWebIdentity"]
      effect  = "Allow"

      condition {
        test     = "StringLike"
        variable = "${replace(statement.value.open_id_url, "https://", "")}:sub"
        values   = ["system:serviceaccount:${statement.value.namespace}:${statement.value.service_name}"]
      }

      principals {
        identifiers = [statement.value.open_id_arn]
        type        = "Federated"
      }
    }
  }

  dynamic "statement" {
    for_each = var.allowed_iams
    content {
      actions = ["sts:AssumeRole"]
      effect  = "Allow"
      principals {
        identifiers = [statement.value]
        type        = "AWS"
      }
    }
  }

  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      identifiers = ["events.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "role" {
  assume_role_policy = data.aws_iam_policy_document.iam_trusts.json
  name               = "${var.env_name}-${var.layer_name}-${var.module_name}"
}

resource "aws_iam_role_policy_attachment" "vanilla_role_attachment" {
  policy_arn = aws_iam_policy.vanilla_policy.arn
  role       = aws_iam_role.role.name
}

resource "aws_iam_role_policy_attachment" "extra_policies_attachment" {
  count      = length(var.extra_iam_policies)
  policy_arn = var.extra_iam_policies[count.index]
  role       = aws_iam_role.role.name
}

resource "aws_iam_role_policy" "pass_role_to_self" {
  role   = aws_iam_role.role.id
  policy = data.aws_iam_policy_document.pass_role_to_self.json
}

data "aws_iam_policy_document" "pass_role_to_self" {
  statement {
    sid    = "AllowToPassSelf"
    effect = "Allow"
    actions = [
      "iam:GetRole",
      "iam:PassRole"
    ]
    resources = [aws_iam_role.role.arn]
  }
}
