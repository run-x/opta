provider "kubernetes" {
  config_path    = var.kubeconfig
  config_context  = var.kubecontext
}

resource "kubernetes_manifest" "manifest" {
  manifest = yamldecode(file(var.file_path))
  timeouts {
    update = "2m"
    create = "5m"
    delete = "2m"
  }
}