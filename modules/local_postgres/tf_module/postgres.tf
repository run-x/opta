terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 1.13.3"
    }
  }
}
resource "helm_release" "opta-local-postgresql" {
  name             = "opta-local-postgres"
  repository       = "https://charts.bitnami.com/bitnami"
  chart            = "postgresql"
  version          = "11.6.5"
  create_namespace = true
  namespace        = var.paasns

  set {
    name  = "postgresqlUsername"
    value = var.db_user
  }
  set {
    name  = "postgresqlPassword"
    value = var.db_password
  }
  set {
    name  = "postgresqlDatabase"
    value = var.db_name
  }
}



