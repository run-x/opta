# https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/eks_node_group
# https://docs.aws.amazon.com/eks/latest/userguide/create-node-role.html
data "aws_iam_policy_document" "node_group" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      identifiers = ["ec2.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "node_group" {
  name = "opta-${var.layer_name}-eks-${var.module_name}-node-group"

  assume_role_policy = data.aws_iam_policy_document.node_group.json
  tags = {
    terraform = "true"
  }
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKSWorkerNodePolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEKS_CNI_Policy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy"
  role       = aws_iam_role.node_group.name
}

resource "aws_iam_role_policy_attachment" "node_group_AmazonEC2ContainerRegistryReadOnly" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
  role       = aws_iam_role.node_group.name
}

resource "random_id" "key_suffix" {
  byte_length = 8
  keepers = {
    spot_instances     = var.spot_instances
    node_disk_size     = var.node_disk_size
    node_instance_type = var.node_instance_type
  }
}

resource "aws_eks_node_group" "node_group" {
  cluster_name    = data.aws_eks_cluster.main.name
  node_group_name = "opta-${var.layer_name}-${var.module_name}-${random_id.key_suffix.hex}"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = data.aws_eks_cluster.main.vpc_config[0].subnet_ids
  capacity_type   = var.spot_instances ? "SPOT" : "ON_DEMAND"

  ami_type = var.ami_type

  disk_size      = var.node_disk_size
  instance_types = [var.node_instance_type]
  labels         = merge(local.default_labels, var.labels)

  scaling_config {
    max_size     = var.max_nodes
    desired_size = max(var.min_nodes, 1)
    min_size     = var.min_nodes
  }

  dynamic "taint" {
    for_each = var.taints
    content {
      key    = taint.value["key"]
      effect = lookup(taint.value, "effect", "NO_SCHEDULE")
      value  = lookup(taint.value, "value", "opta")
    }
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
  ]

  # Optional: Allow external changes without Terraform plan difference
  lifecycle {
    ignore_changes        = [scaling_config[0].desired_size, node_group_name, subnet_ids]
    create_before_destroy = true
  }

  tags = {
    terraform = "true"
  }
}