resource "helm_release" "external-dns" {
  chart = "external-dns"
  name = "external-dns"
  repository = "https://charts.bitnami.com/bitnami"
  namespace = "external-dns"
  create_namespace = true
  atomic = true
  cleanup_on_fail = true
  version = "3.7.0"
  values = [
    yamlencode({
      provider: "aws"
      aws: {
        zoneType: var.zone_type
      }
      txtOwnerId: var.hosted_zone_id
      domainFilters: [var.domain]
      serviceAccount: {
        name: "external-dns"
        annotations: {
          "eks.amazonaws.com/role-arn": aws_iam_role.external_dns.arn
        }
      }
    })
  ]
}