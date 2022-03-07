output "k8s_endpoint" {
  value = aws_eks_cluster.cluster.endpoint
}

output "k8s_ca_data" {
  value = aws_eks_cluster.cluster.certificate_authority[0].data
}

output "k8s_cluster_name" {
  value = aws_eks_cluster.cluster.name
}

output "k8s_openid_provider_url" {
  value = aws_iam_openid_connect_provider.cluster.url
}

output "k8s_openid_provider_arn" {
  value = aws_iam_openid_connect_provider.cluster.arn
}

output "k8s_node_group_security_id" {
  value = aws_eks_cluster.cluster.vpc_config[0].cluster_security_group_id
}

output "k8s_version" {
  value = aws_eks_cluster.cluster.version
}
