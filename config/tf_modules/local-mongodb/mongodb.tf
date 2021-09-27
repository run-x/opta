terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 1.13.3"
    }
  }
}
resource "helm_release" "opta-local-mongodb" {
  name             = "opta-local-mongodb"
  repository       = "https://charts.bitnami.com/bitnami"
  chart            = "mongodb"
  version          = "10.26.3"
  create_namespace = true
  namespace        = var.paasns

  set {
    name  = "auth.username"
    value = var.db_user
  }
  set {
    name  = "auth.password"
    value = var.db_password
  }
  set {
    name  = "auth.database"
    value = var.db_name
  }

}



