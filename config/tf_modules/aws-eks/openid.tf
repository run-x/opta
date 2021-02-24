# NOTE: there is a bug with the thumbprint retrieval, which has been reported on github and we are using the suggested
# workaround:
# https://github.com/terraform-providers/terraform-provider-aws/issues/10104
data "external" "thumbprint" {
  program = [
    "/bin/bash",
    "${path.module}/thumbprint.sh",
    data.aws_region.current.name,
  ]
}

resource "aws_iam_openid_connect_provider" "cluster" {
  client_id_list = ["sts.amazonaws.com"]
  thumbprint_list = [
    data.external.thumbprint.result.thumbprint,
  ]
  url = aws_eks_cluster.cluster.identity[0].oidc[0].issuer
}
