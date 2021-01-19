resource "aws_ecr_repository" "repo" {
  count = var.external_image ? 0 : 1
  name = var.name
  tags = {
    terraform = "true"
  }
}

data "aws_iam_policy_document" "repo_policy" {
  statement {
    sid = "AllowAllFromAccount"

    principals {
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
      type        = "AWS"
    }

    actions = [
      "ecr:*"
    ]
  }
}

resource "aws_ecr_repository_policy" "repo_policy" {
  count = var.external_image ? 0 : 1
  policy     = data.aws_iam_policy_document.repo_policy.json
  repository = aws_ecr_repository.repo[0].name
}

resource "aws_ecr_lifecycle_policy" "repo_policy" {
  count = var.external_image ? 0 : 1
  policy     = file("${path.module}/simple_lifecycle_policy.json")
  repository = aws_ecr_repository.repo[0].name
}
