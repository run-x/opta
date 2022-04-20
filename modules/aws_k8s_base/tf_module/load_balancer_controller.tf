data "aws_iam_policy_document" "load_balancer" {
  statement {
    sid    = "0"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]
    actions   = ["iam:CreateServiceLinkedRole"]

    condition {
      test     = "StringEquals"
      variable = "iam:AWSServiceName"
      values   = ["elasticloadbalancing.amazonaws.com"]
    }
  }
  #tfsec:ignore:aws-iam-no-policy-wildcards
  statement {
    sid    = "1"
    effect = "Allow"
    #Ignore 
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]

    actions = [
      "ec2:DescribeAccountAttributes",
      "ec2:DescribeAddresses",
      "ec2:DescribeAvailabilityZones",
      "ec2:DescribeInternetGateways",
      "ec2:DescribeVpcs",
      "ec2:DescribeVpcPeeringConnections",
      "ec2:DescribeSubnets",
      "ec2:DescribeSecurityGroups",
      "ec2:DescribeInstances",
      "ec2:DescribeNetworkInterfaces",
      "ec2:DescribeTags",
      "ec2:GetCoipPoolUsage",
      "ec2:DescribeCoipPools",
      "elasticloadbalancing:DescribeLoadBalancers",
      "elasticloadbalancing:DescribeLoadBalancerAttributes",
      "elasticloadbalancing:DescribeListeners",
      "elasticloadbalancing:DescribeListenerCertificates",
      "elasticloadbalancing:DescribeSSLPolicies",
      "elasticloadbalancing:DescribeRules",
      "elasticloadbalancing:DescribeTargetGroups",
      "elasticloadbalancing:DescribeTargetGroupAttributes",
      "elasticloadbalancing:DescribeTargetHealth",
      "elasticloadbalancing:DescribeTags",
    ]
  }

  statement {
    sid    = "2"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]

    actions = [
      "cognito-idp:DescribeUserPoolClient",
      "acm:ListCertificates",
      "acm:DescribeCertificate",
      "iam:ListServerCertificates",
      "iam:GetServerCertificate",
      "waf-regional:GetWebACL",
      "waf-regional:GetWebACLForResource",
      "waf-regional:AssociateWebACL",
      "waf-regional:DisassociateWebACL",
      "wafv2:GetWebACL",
      "wafv2:GetWebACLForResource",
      "wafv2:AssociateWebACL",
      "wafv2:DisassociateWebACL",
      "shield:GetSubscriptionState",
      "shield:DescribeProtection",
      "shield:CreateProtection",
      "shield:DeleteProtection",
    ]
  }

  statement {
    sid    = "3"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]

    actions = [
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupIngress",
    ]
  }

  statement {
    sid    = "4"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]
    actions   = ["ec2:CreateSecurityGroup"]
  }

  statement {
    sid    = "5"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["arn:aws:ec2:*:*:security-group/*"]
    actions   = ["ec2:CreateTags"]

    condition {
      test     = "StringEquals"
      variable = "ec2:CreateAction"
      values   = ["CreateSecurityGroup"]
    }

    condition {
      test     = "Null"
      variable = "aws:RequestTag/elbv2.k8s.aws/cluster"
      values   = ["false"]
    }
  }

  #Ignore 
  #tfsec:ignore:aws-iam-no-policy-wildcards
  statement {
    sid    = "6"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["arn:aws:ec2:*:*:security-group/*"]

    actions = [
      "ec2:CreateTags",
      "ec2:DeleteTags",
    ]

    condition {
      test     = "Null"
      variable = "aws:RequestTag/elbv2.k8s.aws/cluster"
      values   = ["true"]
    }

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/elbv2.k8s.aws/cluster"
      values   = ["false"]
    }
  }

  statement {
    sid    = "7"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]

    actions = [
      "ec2:AuthorizeSecurityGroupIngress",
      "ec2:RevokeSecurityGroupIngress",
      "ec2:DeleteSecurityGroup",
    ]

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/elbv2.k8s.aws/cluster"
      values   = ["false"]
    }
  }

  statement {
    sid    = "8"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]

    actions = [
      "elasticloadbalancing:CreateLoadBalancer",
      "elasticloadbalancing:CreateTargetGroup",
    ]

    condition {
      test     = "Null"
      variable = "aws:RequestTag/elbv2.k8s.aws/cluster"
      values   = ["false"]
    }
  }
  #tfsec:ignore:aws-iam-no-policy-wildcards
  statement {
    sid       = "9"
    effect    = "Allow"
    resources = ["*"]

    actions = [
      "elasticloadbalancing:CreateListener",
      "elasticloadbalancing:DeleteListener",
      "elasticloadbalancing:CreateRule",
      "elasticloadbalancing:DeleteRule",
    ]
  }
  #Ignore 
  #tfsec:ignore:aws-iam-no-policy-wildcards
  statement {
    sid    = "10"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = [
      "arn:aws:elasticloadbalancing:*:*:targetgroup/*/*",
      "arn:aws:elasticloadbalancing:*:*:loadbalancer/net/*/*",
      "arn:aws:elasticloadbalancing:*:*:loadbalancer/app/*/*",
    ]

    actions = [
      "elasticloadbalancing:AddTags",
      "elasticloadbalancing:RemoveTags",
    ]

    condition {
      test     = "Null"
      variable = "aws:RequestTag/elbv2.k8s.aws/cluster"
      values   = ["true"]
    }

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/elbv2.k8s.aws/cluster"
      values   = ["false"]
    }
  }

  statement {
    sid    = "11"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = [
      "arn:aws:elasticloadbalancing:*:*:listener/net/*/*/*",
      "arn:aws:elasticloadbalancing:*:*:listener/app/*/*/*",
      "arn:aws:elasticloadbalancing:*:*:listener-rule/net/*/*/*",
      "arn:aws:elasticloadbalancing:*:*:listener-rule/app/*/*/*",
    ]

    actions = [
      "elasticloadbalancing:AddTags",
      "elasticloadbalancing:RemoveTags",
    ]
  }

  statement {
    sid    = "12"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]

    actions = [
      "elasticloadbalancing:ModifyLoadBalancerAttributes",
      "elasticloadbalancing:SetIpAddressType",
      "elasticloadbalancing:SetSecurityGroups",
      "elasticloadbalancing:SetSubnets",
      "elasticloadbalancing:DeleteLoadBalancer",
      "elasticloadbalancing:ModifyTargetGroup",
      "elasticloadbalancing:ModifyTargetGroupAttributes",
      "elasticloadbalancing:DeleteTargetGroup",
    ]

    condition {
      test     = "Null"
      variable = "aws:ResourceTag/elbv2.k8s.aws/cluster"
      values   = ["false"]
    }
  }
  #tfsec:ignore:aws-iam-no-policy-wildcards
  statement {
    sid       = "13"
    effect    = "Allow"
    resources = ["arn:aws:elasticloadbalancing:*:*:targetgroup/*/*"]

    actions = [
      "elasticloadbalancing:RegisterTargets",
      "elasticloadbalancing:DeregisterTargets",
    ]
  }

  statement {
    sid    = "14"
    effect = "Allow"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]

    actions = [
      "elasticloadbalancing:SetWebAcl",
      "elasticloadbalancing:ModifyListener",
      "elasticloadbalancing:AddListenerCertificates",
      "elasticloadbalancing:RemoveListenerCertificates",
      "elasticloadbalancing:ModifyRule",
    ]
  }
}

resource "aws_iam_policy" "load_balancer" {
  name   = "opta-${var.env_name}-albc"
  policy = data.aws_iam_policy_document.load_balancer.json
}

data "aws_iam_policy_document" "trust_k8s_openid_alb" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]
    effect  = "Allow"

    condition {
      test     = "StringEquals"
      variable = "${replace(var.openid_provider_url, "https://", "")}:sub"
      values   = ["system:serviceaccount:kube-system:aws-load-balancer-controller"]
    }

    principals {
      identifiers = [var.openid_provider_arn]
      type        = "Federated"
    }
  }
}

resource "aws_iam_role" "load_balancer" {
  assume_role_policy = data.aws_iam_policy_document.trust_k8s_openid_alb.json
  name               = "opta-${var.env_name}-albc"
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
      clusterName : var.eks_cluster_name,
      region : data.aws_region.current.id,
      serviceAccount : {
        annotations : {
          "eks.amazonaws.com/role-arn" : aws_iam_role.load_balancer.arn
        }
        name : "aws-load-balancer-controller"
      },
      region : data.aws_region.current.name
    })
  ]
  namespace        = "kube-system"
  create_namespace = true
  cleanup_on_fail  = true
  atomic           = true
  wait_for_jobs    = false
  version          = "1.4.1"
  depends_on = [
    aws_iam_role_policy_attachment.load_balancer
  ]
}

