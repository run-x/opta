resource "aws_security_group" "eks" {
  name_prefix = "opta-${var.layer_name}"
  description = "EKS cluster security group."
  vpc_id      = var.vpc_id

  tags = {
    "Name" = "opta-${var.layer_name}-eks_cluster_sg"
  }

  ingress {
    description = "allowallfromself"
    from_port   = 0
    protocol    = "-1"
    to_port     = 0
    self        = true
  }

  egress {
    description = "alloutbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    # To be fixed - for now user can create an SG manually to override.
    #tfsec:ignore:aws-vpc-no-public-egress-sgr
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_eks_cluster" "cluster" {
  name     = var.cluster_name
  role_arn = aws_iam_role.cluster_role.arn
  version  = var.k8s_version

  # To be fixed, although early opta users need this - Cluster allows access from a public CIDR: 0.0.0.0/0
  #tfsec:ignore:aws-eks-no-public-cluster-access-to-cidr
  vpc_config {
    subnet_ids              = var.private_subnet_ids
    security_group_ids      = [aws_security_group.eks.id]
    endpoint_private_access = false # TODO: make this true once we got VPN figured out
    #tfsec:ignore:aws-eks-no-public-cluster-access
    endpoint_public_access = true # TODO: make this false once we got VPN figured out
  }

  encryption_config {
    resources = ["secrets"]
    provider {
      key_arn = data.aws_kms_key.env_key.arn
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
    ignore_changes = [vpc_config[0].security_group_ids]
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
  name              = "/aws/eks/opta-${var.layer_name}/cluster"
  kms_key_id        = data.aws_kms_key.env_key.arn
  retention_in_days = var.eks_log_retention
  tags = {
    terraform = "true"
  }
  lifecycle {
    ignore_changes = [name]
  }
}
