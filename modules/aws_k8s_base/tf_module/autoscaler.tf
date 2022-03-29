data "aws_iam_policy_document" "autoscaler" {
#Ignore 
#tfsec:ignore:aws-iam-no-policy-wildcards
  statement {
    actions = [
      "autoscaling:DescribeAutoScalingGroups",
      "autoscaling:DescribeAutoScalingInstances",
      "autoscaling:DescribeLaunchConfigurations",
      "autoscaling:DescribeTags",
      "autoscaling:SetDesiredCapacity",
      "autoscaling:TerminateInstanceInAutoScalingGroup",
      "ec2:DescribeLaunchTemplateVersions",
      "ec2:DescribeInstanceTypes"
    ]
    resources = ["*"]
    sid       = "autoscaling"
  }
}

resource "aws_iam_policy" "autoscaler" {
  name   = "opta-${var.env_name}-k8s-autoscaler"
  policy = data.aws_iam_policy_document.autoscaler.json
}

data "aws_iam_policy_document" "trust_k8s_openid" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:autoscaler:autoscaler"]
    }

    principals {
      identifiers = [var.openid_provider_arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "autoscaler" {
  assume_role_policy = data.aws_iam_policy_document.trust_k8s_openid.json
  name               = "opta-${var.env_name}-k8s-autoscaler"
}

resource "aws_iam_role_policy_attachment" "autoscaler" {
  policy_arn = aws_iam_policy.autoscaler.arn
  role       = aws_iam_role.autoscaler.name
}

resource "helm_release" "autoscaler" {
  chart      = "cluster-autoscaler"
  name       = "cluster-autoscaler"
  repository = "https://kubernetes.github.io/autoscaler"
  values = [
    yamlencode({
      extraArgs : { "skip-nodes-with-local-storage" : false }
      autoDiscovery : {
        clusterName : var.eks_cluster_name
      },
      rbac : {
        serviceAccount : {
          annotations : {
            "eks.amazonaws.com/role-arn" : aws_iam_role.autoscaler.arn
          }
          name : "autoscaler"
        }
      }
      awsRegion : data.aws_region.current.name
    })
  ]
  namespace        = "autoscaler"
  create_namespace = true
  cleanup_on_fail  = true
  atomic           = true
  wait_for_jobs    = false
}