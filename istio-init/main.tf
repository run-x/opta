# https://istio.io/latest/docs/setup/install/operator/
resource "helm_release" "istio-operator" {
  chart = "${path.module}/istio-operator"
  name = "istio-operator"
  cleanup_on_fail = true
  atomic = true
  set {
    name = "tag"
    value = "1.8.1"
  }
  set {
    name = "hub"
    value = "docker.io/istio"
  }
  set {
    name = "operatorNamespace"
    value = "istio-operator"
  }
  namespace = "default"
}

resource "helm_release" "istio-vanilla-profile" {
  chart = "${path.module}/istio-vanilla-profile"
  name = "istio-vanilla-profile"
  namespace = "istio-system"
  cleanup_on_fail = true
  atomic = true
  depends_on = [helm_release.istio-operator]
  create_namespace = true
  values = [
    yamlencode({
      domain_names: var.domain_names
      ssl_cert_arn: var.acm_cert_arn
    })
  ]
}

resource "helm_release" "istio-extras" {
  chart = "${path.module}/istio-extras"
  name = "istio-extras"
  namespace = "istio-system"
  cleanup_on_fail = true
  atomic = true
  values = [
    yamlencode({
      main_gateway: {
        domain_names: var.domain_names
      }
    })
  ]
  depends_on = [helm_release.istio-vanilla-profile]
}