terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = ">= 1.13.3"
    }
  }
}

resource "helm_release" "k8s-service" {
  chart = "${path.module}/k8s-service"
  name  = "${var.layer_name}-${var.module_name}"
  values = [
    yamlencode({
      deployment_timestamp : timestamp()
      autoscaling : {
        minReplicas : var.min_containers,
        maxReplicas : var.min_containers,
        targetCPUUtilizationPercentage : var.autoscaling_target_cpu_percentage
        targetMemoryUtilizationPercentage : var.autoscaling_target_mem_percentage
      },
      port : var.port,
      containerResourceLimits : {
        cpu : "${var.resource_request["cpu"] * 2}m"
        memory : "${var.resource_request["memory"] * 2}Mi"
      },
      containerResourceRequests : {
        cpu : "${var.resource_request["cpu"]}m"
        memory : "${var.resource_request["memory"]}Mi"
      },
      deployPods : (var.image != "AUTO") || (var.tag != null),
      image : var.image == "AUTO" ? (var.tag == null ? "" : "${var.acr_registry_name}.azurecr.io/${var.layer_name}/${var.module_name}:${var.tag}") : (var.tag == null ? var.image : "${var.image}:${var.tag}")
      version : var.tag == null ? "latest" : var.tag
      livenessProbePath : var.healthcheck_path == null || var.liveness_probe_path != "/healthcheck" ? var.liveness_probe_path : var.healthcheck_path,
      readinessProbePath : var.healthcheck_path == null || var.readiness_probe_path != "/healthcheck" ? var.readiness_probe_path : var.healthcheck_path,
      envVars : var.env_vars,
      linkSecrets : var.link_secrets,
      manualSecrets : var.manual_secrets,
      uriComponents : local.uri_components,
      layerName : var.layer_name,
      moduleName : var.module_name,
      environmentName : var.env_name,
    })
  ]
  atomic          = true
  cleanup_on_fail = true
}

