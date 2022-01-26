resource "random_string" "repo_name_hash" {
  length  = 4
  special = false
  upper   = false
}

resource "aws_ecr_repository" "repo" {
  count = local.uppercase_image == "AUTO" ? 1 : 0
  name  = "opta-${var.layer_name}-${var.module_name}-${random_string.repo_name_hash.result}"
  tags = {
    terraform = "true"
  }
  lifecycle {
    ignore_changes = [name]
  }
}

data "aws_ecr_image" "service_image" {
  count           = local.uppercase_image == "AUTO" && var.tag != "" && var.tag != null ? 1 : 0
  repository_name = aws_ecr_repository.repo[0].name
  image_tag       = var.tag
  image_digest    = var.digest
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
  count      = local.uppercase_image == "AUTO" ? 1 : 0
  policy     = data.aws_iam_policy_document.repo_policy.json
  repository = aws_ecr_repository.repo[0].name
}

resource "aws_ecr_lifecycle_policy" "repo_policy" {
  count      = local.uppercase_image == "AUTO" ? 1 : 0
  policy     = file("${path.module}/simple_lifecycle_policy.json")
  repository = aws_ecr_repository.repo[0].name
}
