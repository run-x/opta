data "aws_iam_policy_document" "external_dns" {
  count = var.enable_external_dns ? 1 : 0
  statement {
    sid       = "ChangeResourceRecordSets"
    resources = ["arn:aws:route53:::hostedzone/*"]
    actions   = ["route53:ChangeResourceRecordSets"]
  }
  statement {
    sid       = "DescribeRoute53"
    resources = ["*"]
    actions = [
      "route53:ListHostedZones",
      "route53:ListResourceRecordSets"
    ]
  }
}

resource "aws_iam_policy" "external_dns" {
  count  = var.enable_external_dns ? 1 : 0
  name   = "opta-${var.env_name}-external-dns"
  policy = data.aws_iam_policy_document.external_dns[0].json
}

data "aws_iam_policy_document" "external_dns_trust" {
  count = var.enable_external_dns ? 1 : 0
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    condition {
      test     = "StringEquals"
      values   = ["system:serviceaccount:external-dns:external-dns"]
      variable = "${replace(var.openid_provider_url, "https://", "")}:sub"
    }
    principals {
      identifiers = [var.openid_provider_arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "external_dns" {
  count              = var.enable_external_dns ? 1 : 0
  name               = "opta-${var.env_name}-external-dns"
  assume_role_policy = data.aws_iam_policy_document.external_dns_trust[0].json
}

resource "aws_iam_role_policy_attachment" "external_dns" {
  count      = var.enable_external_dns ? 1 : 0
  policy_arn = aws_iam_policy.external_dns[0].arn
  role       = aws_iam_role.external_dns[0].name
}

resource "helm_release" "external-dns" {
  count            = var.enable_external_dns ? 1 : 0
  chart            = "external-dns"
  name             = "external-dns"
  repository       = "https://charts.bitnami.com/bitnami"
  namespace        = "external-dns"
  create_namespace = true
  atomic           = true
  cleanup_on_fail  = true
  version          = "6.2.1"
  values = [
    yamlencode({
      provider : "aws"
      aws : {
        zoneType : "public"
      }
      domainFilters : [var.domain]
      serviceAccount : {
        name : "external-dns"
        annotations : {
          "eks.amazonaws.com/role-arn" : aws_iam_role.external_dns[0].arn
        }
      }
    })
  ]
}