resource "helm_release" "opta_base" {
  chart     = "${path.module}/opta-base"
  name      = "opta-base"
  namespace = "default"
  values = [
    yamlencode({
      adminArns : var.admin_arns
      deployment_timestamp : timestamp()
    })
  ]
  depends_on = [
    helm_release.cert_manager
  ]
}