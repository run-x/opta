
resource "aws_iam_policy" "load_balancer" {
  name        = "load-balancer-controller"
  description = "Policy for the AWS Load Balancer Controller"
  policy      = file("aws-lb-iam-policy.json")
}

data "aws_iam_policy_document" "trust_k8s_openid_alb" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.oidc_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    principals {
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:oidc-provider/${replace(var.oidc_provider_url, "https://", "")}"]

      type = "Federated"
    }
  }
}

resource "aws_iam_role" "load_balancer" {
  assume_role_policy = data.aws_iam_policy_document.trust_k8s_openid_alb.json
  name               = "load-balancer-controller"
}

resource "aws_iam_role_policy_attachment" "load_balancer" {
  policy_arn = aws_iam_policy.load_balancer.arn
  role       = aws_iam_role.load_balancer.name
}


resource "helm_release" "load_balancer" {
  chart      = "aws-load-balancer-controller"
  name       = "aws-load-balancer-controller"
  repository = "https://aws.github.io/eks-charts"
  values = [
    yamlencode({
      clusterName : var.cluster_name,
      serviceAccount : {
        annotations : {
          "eks.amazonaws.com/role-arn" : aws_iam_role.load_balancer.arn
        }
        name : "aws-load-balancer-controller"
      },
      region : data.aws_region.current.name
    })
  ]
  namespace       = "kube-system"
  cleanup_on_fail = true
  atomic          = true
  wait_for_jobs   = false
  version         = "1.4.0"
}
