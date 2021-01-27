# https://docs.aws.amazon.com/eks/latest/userguide/service_IAM_role.html
data "aws_iam_policy_document" "trust_policy" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      identifiers = ["eks.amazonaws.com"]
      type        = "Service"
    }
  }
}

resource "aws_iam_role" "cluster_role" {
  name               = "eks-${var.cluster_name}-cluster-role"
  assume_role_policy = data.aws_iam_policy_document.trust_policy.json
  tags = {
    terraform = "true"
  }
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster_role.name
}
