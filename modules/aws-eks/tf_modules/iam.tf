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
  name               = "opta-${var.layer_name}-eks-cluster-role"
  assume_role_policy = data.aws_iam_policy_document.trust_policy.json
  tags = {
    terraform = "true"
  }
}

resource "aws_iam_role_policy_attachment" "cluster_AmazonEKSClusterPolicy" {
  policy_arn = "arn:aws:iam::aws:policy/AmazonEKSClusterPolicy"
  role       = aws_iam_role.cluster_role.name
}

data "aws_iam_policy_document" "minimal_ebs_kms_create_and_attach" {
  statement {
    sid = "MinimalEBSKMSCreateAndAttach"
    actions = [
      "kms:Decrypt",
      "kms:GenerateDataKeyWithoutPlaintext",
      "kms:CreateGrant"
    ]
    resources = [data.aws_kms_key.env_key.arn]
  }
}

resource "aws_iam_policy" "minimal_ebs_kms_create_and_attach" {
  name = "opta-${var.layer_name}-ebs-kms-create-attach"

  policy = data.aws_iam_policy_document.minimal_ebs_kms_create_and_attach.json
}

resource "aws_iam_role_policy_attachment" "cluster_minimal_ebs_kms_create_and_attache" {
  policy_arn = aws_iam_policy.minimal_ebs_kms_create_and_attach.arn
  role       = aws_iam_role.cluster_role.name
}
