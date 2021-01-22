terraform {
  required_providers {
    helm = {
      source = "hashicorp/helm"
      version = ">= 2.0.2"
    }
  }
}

resource "random_password" "cluster_agent_token" {
  length = 16
  special = false
}

resource "helm_release" "datadog" {
  count = (var.api_key == null || var.api_key == "") ? 0 : 1
  repository = "https://helm.datadoghq.com"
  chart = "datadog"
  name = var.name

  values = [
    yamlencode({
      rbac: {
        create: true
      }
      datadog: {
        leaderElection: true
        collectEvents: true

        logs: {
          enabled: true
          containerCollectAll: true
        }

        apm: {
          enabled: true
        }
        podLabelsAsTags: {
          app: "kube_app"
          release: "helm_release"
        }
      }
      clusterAgent: {
        enabled: true
        token: random_password.cluster_agent_token.result
        metricsProvider: {
          enabled: true
        }
        admissionController: {
          enabled: true
          mutateUnlabelled: true
        }
      }
    })
  ]


  set {
    name  = "datadog.apiKey"
    value = var.api_key
  }

  namespace = "datadog"
  create_namespace = true
  atomic          = true
  cleanup_on_fail = true
  recreate_pods   = true
}

