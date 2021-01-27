resource "aws_eks_node_group" "node_group" {
  cluster_name    = var.cluster_name
  node_group_name = var.node_group_name
  node_role_arn   = aws_iam_role.node_group.arn
  subnet_ids      = data.aws_eks_cluster.current.vpc_config[0].subnet_ids

  # Yes, Graviton2 AL2_ARM_64 option is available, but I'm not considering it right now because it's really new, and
  # the release post mentioned the need to be multi-arched ready, which I'm not dealing with.
  # https://aws.amazon.com/blogs/containers/eks-on-graviton-generally-available/
  ami_type = var.use_gpu ? "AL2_x86_64_GPU" : "AL2_x86_64"

  disk_size      = var.disk_size
  instance_types = [var.instance_type]
  labels         = merge({ node_group_name = var.node_group_name }, var.node_labels)

  dynamic "remote_access" {
    for_each = var.ssh_key == "" ? [] : [true]
    content {
      ec2_ssh_key               = var.ssh_key
      source_security_group_ids = var.ssh_security_group_ids
    }
  }
  scaling_config {
    desired_size = var.desired_size
    max_size     = var.max_size
    min_size     = var.min_size
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
    ignore_changes = [scaling_config[0].desired_size]
  }

  tags = {
    terraform = "true"
  }
}