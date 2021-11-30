resource "aws_iam_policy" "vanilla_policy" {
  name   = "${var.env_name}-${var.layer_name}-${var.module_name}"
  policy = jsonencode(var.iam_policy)
}

resource "aws_iam_user" "user" {
  name = "${var.env_name}-${var.layer_name}-${var.module_name}"
}

resource "aws_iam_user_policy_attachment" "vanilla_role_attachment" {
  policy_arn = aws_iam_policy.vanilla_policy.arn
  user       = aws_iam_user.user.name
}

resource "aws_iam_user_policy_attachment" "extra_policies_attachment" {
  count      = length(var.extra_iam_policies)
  policy_arn = var.extra_iam_policies[count.index]
  user       = aws_iam_user.user.name
}

resource "aws_iam_user_policy" "pass_role_to_self" {
  policy = data.aws_iam_policy_document.pass_role_to_self.json
  user   = aws_iam_user.user.id
}

data "aws_iam_policy_document" "pass_role_to_self" {
  statement {
    sid    = "AllowToPassSelf"
    effect = "Allow"
    actions = [
      "iam:GetRole",
      "iam:PassRole"
    ]
    resources = [aws_iam_user.user.arn]
  }
}