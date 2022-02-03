terraform {
  required_providers {
    helm = {
      source  = "hashicorp/helm"
      version = ">= 2.3.0"
    }
  }
}

resource "random_password" "cluster_agent_token" {
  length  = 32
  special = false
}

resource "helm_release" "datadog" {
  count      = (var.api_key == null || var.api_key == "") ? 0 : 1
  repository = "https://helm.datadoghq.com"
  chart      = "datadog"
  name       = "${var.layer_name}-${var.module_name}"
  version    = var.chart_version
  values = [
    yamlencode({
      datadog : {
        collectEvents : true
        leaderElection : true
        env : [
          {
            name : "DD_ENV"
            value : var.layer_name
          }
        ]
        dogstatsd : {
          useHostPort : true
          nonLocalTraffic : true
        }
        logs : {
          enabled : true
          containerCollectAll : true
        }
        clusterName : var.layer_name

        apm : {
          portEnabled : true
        }
        podLabelsAsTags : {
          app : "kube_app"
          release : "helm_release"
        }
      }
      clusterAgent : {
        useHostNetwork : true
        enabled : true
        token : random_password.cluster_agent_token.result
        admissionController : {
          enabled : true
          mutateUnlabelled : true
        }
      }
    }),
    yamlencode(var.values)
  ]


  set {
    name  = "datadog.apiKey"
    value = var.api_key
  }

  namespace        = "datadog"
  create_namespace = true
  atomic           = true
  cleanup_on_fail  = true
  recreate_pods    = true
  timeout          = var.timeout
}

