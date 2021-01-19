terraform {
  required_providers {
    kubernetes = {
      source = "hashicorp/kubernetes"
      version = ">= 1.13.3"
    }
  }
}

resource "helm_release" "k8s-service" {
  chart = "${path.module}/k8s-service"
  name = var.name
  namespace = var.namespace
  values = [
    yamlencode({
      autoscaling: {
        minReplicas: var.min_autoscaling,
        maxReplicas: var.max_autoscaling,
        targetCPUUtilizationPercentage: var.autoscaling_cpu_percentage_threshold
        targetMemoryUtilizationPercentage: var.autoscaling_mem_percentage_threshold
      },
      port: var.target_port,
      podResourceLimits: var.pod_resource_limits,
      podResourceRequests: var.pod_resource_requests,
      image: {
        repository: var.external_image ? var.image : "${aws_ecr_repository.repo[0].repository_url}/${var.image}"
        tag: var.tag
      },
      livenessProbePath: var.liveness_probe_path,
      readinessProbePath: var.readiness_probe_path,
      envVars: var.env_vars,
      domain: var.domain,
      uriPrefix: var.uri_prefix
      blah: 2
    })
  ]
  atomic          = true
  cleanup_on_fail = true
  recreate_pods   = true
}

