terraform {
  required_providers {
    helm = {
      source = "hashicorp/helm"
      version = ">= 2.0.2"
    }
  }
}

resource "helm_release" "datadog" {
  count = var.api_key == null ? 0 : 1
  repository = "https://helm.datadoghq.com"
  chart = "datadog"
  name = var.name

  values = [
    file("${path.module}/values.yml")
  ]


  set {
    name  = "datadog.apiKey"
    value = var.api_key
  }

  atomic          = true
  cleanup_on_fail = true
  recreate_pods   = true
}

