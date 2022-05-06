provider "kubernetes" {
  config_path    = var.kubeconfig
  config_context = var.kubecontext
}

resource "helm_release" "manifest" {
  name       = "${var.layer_name}-${var.module_name}"
  repository = "https://charts.itscontained.io"
  chart      = "raw"
  version    = "0.2.5"
  values = [file(var.file_path)]
}