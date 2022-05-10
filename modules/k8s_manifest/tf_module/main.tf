provider "kubernetes" {
  host                   = var.host
  token                  = var.token
  cluster_ca_certificate = var.cluster_ca_certificate
  client_certificate     = var.client_certificate
  client_key             = var.client_key
}

resource "kubernetes_manifest" "manifest" {
  manifest = yamldecode(file(var.file_path))
  timeouts {
    update = "5m"
    create = "5m"
    delete = "5m"
  }
}