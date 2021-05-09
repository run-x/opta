resource "aws_iam_policy" "vanilla_policy" {
  name = "${var.env_name}-${var.layer_name}-${var.module_name}"
  policy = jsonencode(var.iam_policy)
}

resource "aws_iam_user" "user" {
  name = "${var.env_name}-${var.layer_name}-${var.module_name}"
}

resource "aws_iam_user_policy_attachment" "vanilla_role_attachment" {
  policy_arn = aws_iam_policy.vanilla_policy.arn
  user = aws_iam_user.user.name
}

resource "aws_iam_user_policy_attachment" "extra_policies_attachment" {
  count = length(var.extra_iam_policies)
  policy_arn = var.extra_iam_policies[count.index]
  user = aws_iam_user.user.name
}
