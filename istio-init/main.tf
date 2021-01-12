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
}