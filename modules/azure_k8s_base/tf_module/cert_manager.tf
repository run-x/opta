resource "helm_release" "cert_manager" {
  chart            = "cert-manager"
  repository       = "https://charts.jetstack.io"
  name             = "cert-manager"
  namespace        = "cert-manager"
  create_namespace = true
  atomic           = true
  cleanup_on_fail  = true
  version          = "1.3.1"
  values = [
    yamlencode({
      installCRDs : true
    }), yamlencode(var.cert_manager_values)
  ]
}