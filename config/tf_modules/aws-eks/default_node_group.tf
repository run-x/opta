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
  name = "opta-${var.layer_name}-eks-default-node-group"

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
    launch_template    = try(var.node_launch_template["user_data"], "")
  }
}

resource "aws_launch_template" "eks_node" {
  count = (length(var.node_launch_template) > 0) ? 1 : 0
  instance_type = var.node_instance_type
  name_prefix = "opta-${var.layer_name}"
  # https://github.com/hashicorp/terraform-provider-aws/issues/15118

  block_device_mappings {
    device_name = "/dev/sda1"

    ebs {
      volume_size = var.node_disk_size + 10
    }
  }

  user_data = base64encode(join("\n" ,[local.user_data_prefix, try(var.node_launch_template["user_data"], ""), local.user_data_suffix]))
}


resource "aws_eks_node_group" "node_group" {
  cluster_name    = aws_eks_cluster.cluster.name
  node_group_name = "opta-${var.layer_name}-default-${random_id.key_suffix.hex}"
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = aws_eks_cluster.cluster.vpc_config[0].subnet_ids
  capacity_type   = var.spot_instances ? "SPOT" : "ON_DEMAND"


  # Yes, Graviton2 AL2_ARM_64 option is available, but I'm not considering it right now because it's really new, and
  # the release post mentioned the need to be multi-arched ready, which I'm not dealing with.
  # https://aws.amazon.com/blogs/containers/eks-on-graviton-generally-available/
  ami_type = "AL2_x86_64"

  disk_size      = (length(var.node_launch_template) > 0) ? null : var.node_disk_size
  instance_types = (length(var.node_launch_template) > 0) ? [] : [var.node_instance_type]
  labels         = { node_group_name = "opta-${var.layer_name}-default" }

  scaling_config {
    max_size     = var.max_nodes
    desired_size = var.min_nodes
    min_size     = var.min_nodes
  }

  # Ensure that IAM Role permissions are created before and deleted after EKS Node Group handling.
  # Otherwise, EKS will not be able to properly delete EC2 Instances and Elastic Network Interfaces.
  depends_on = [
    aws_iam_role_policy_attachment.node_group_AmazonEKSWorkerNodePolicy,
    aws_iam_role_policy_attachment.node_group_AmazonEKS_CNI_Policy,
    aws_iam_role_policy_attachment.node_group_AmazonEC2ContainerRegistryReadOnly,
  ]

  dynamic "launch_template" {
    for_each = (length(aws_launch_template.eks_node) > 0) ? [1] : []
    content {
      id = aws_launch_template.eks_node[0].id
      version = aws_launch_template.eks_node[0].latest_version
    }
  }

  # Optional: Allow external changes without Terraform plan difference
  lifecycle {
    ignore_changes        = [scaling_config[0].desired_size, node_group_name]
    create_before_destroy = true
  }

  tags = {
    terraform = "true"
  }
}
