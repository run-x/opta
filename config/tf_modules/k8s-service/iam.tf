resource "aws_iam_policy" "k8s_service" {
  name   = "${var.env_name}-${var.layer_name}-${var.module_name}"
  policy = jsonencode(var.iam_policy)
}

data "aws_iam_policy_document" "trust_k8s_openid" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:${var.layer_name}:${var.module_name}"]
    }

    principals {
      identifiers = [var.openid_provider_arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "k8s_service" {
  assume_role_policy = data.aws_iam_policy_document.trust_k8s_openid.json
  name               = "${var.env_name}-${var.layer_name}-${var.module_name}"
}

resource "aws_iam_role_policy_attachment" "vanilla_role_attachment" {
  policy_arn = aws_iam_policy.k8s_service.arn
  role       = aws_iam_role.k8s_service.name
}

resource "aws_iam_role_policy_attachment" "extra_policies_attachment" {
  count      = length(var.additional_iam_policies)
  policy_arn = var.additional_iam_policies[count.index]
  role       = aws_iam_role.k8s_service.name
}