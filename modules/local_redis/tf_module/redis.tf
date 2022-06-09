terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 1.13.3"
    }
  }
}
resource "helm_release" "opta-local-redis" {
  name             = "opta-local-redis"
  repository       = "https://charts.bitnami.com/bitnami"
  chart            = "redis"
  version          = "16.12.0"
  create_namespace = true
  namespace        = var.paasns
  set {
    name  = "cluster.enabled"
    value = "false"
  }
  set {
    name  = "auth.enabled"
    value = "false"
  }

  set {
    name  = "metrics.enabled"
    value = "false"
  }
  set {
    name  = "architecture"
    value = "standalone"
  }
}


