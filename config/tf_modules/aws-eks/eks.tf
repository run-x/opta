data "aws_kms_key" "default" {
  key_id = "alias/opta-${var.env_name}"
}

resource "aws_eks_cluster" "cluster" {
  name     = "opta-${var.layer_name}"
  role_arn = aws_iam_role.cluster_role.arn
  version  = var.k8s_version

  vpc_config {
    subnet_ids              = data.aws_subnet_ids.private.ids
    endpoint_private_access = false # TODO: make this true once we got VPN figured out
    endpoint_public_access  = true # TODO: make this false once we got VPN figured out
  }

  encryption_config {
    resources = ["secrets"]
    provider {
      key_arn = data.aws_kms_key.default.arn
    }
  }

  # https://docs.aws.amazon.com/eks/latest/userguide/control-plane-logs.html
  enabled_cluster_log_types = ["api", "audit", "authenticator", "controllerManager", "scheduler"]

  # Ensure that IAM Role permissions are created before and deleted after EKS Cluster handling.
  # Otherwise, EKS will not be able to properly delete EKS managed EC2 infrastructure such as Security Groups.
  depends_on = [
    aws_iam_role_policy_attachment.cluster_AmazonEKSClusterPolicy,
    aws_cloudwatch_log_group.cluster_logs,
  ]

  tags = {
    terraform = "true"
  }
  lifecycle {
    ignore_changes = [
      vpc_config[0].subnet_ids
    ]
  }
}

resource "aws_security_group_rule" "control_plane_access" {
  count                    = length(var.control_plane_security_groups)
  from_port                = 443
  protocol                 = "tcp"
  security_group_id        = aws_eks_cluster.cluster.vpc_config[0].cluster_security_group_id
  source_security_group_id = var.control_plane_security_groups[count.index]
  to_port                  = 443
  type                     = "ingress"
}

resource "aws_cloudwatch_log_group" "cluster_logs" {
  name              = "/eks/opta-${var.layer_name}/cluster"
  retention_in_days = 7
  tags = {
    terraform = "true"
  }
}

data "aws_eks_cluster_auth" "cluster" {
  name = aws_eks_cluster.cluster.name
}