resource "helm_release" "metrics_server" {
  chart = "metrics-server"
  name = "metrics-server"
  repository = "https://charts.bitnami.com/bitnami"
  namespace = "metrics-server"
  create_namespace = true
  atomic = true
  cleanup_on_fail = true
}