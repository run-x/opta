provider "kubernetes" {
  # config_path    = var.kubeconfig
  # config_context = var.kubecontext
https://471D9504BFE9596C4AD736A055C6213A.gr7.us-east-1.eks.amazonaws.com

}

resource "kubernetes_manifest" "manifest" {
  manifest = yamldecode(file(var.file_path))
  timeouts {
    update = "5m"
    create = "5m"
    delete = "5m"
  }
}