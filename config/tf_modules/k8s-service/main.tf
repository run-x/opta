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
  name = "${var.layer_name}-${var.module_name}"
  values = [
    yamlencode({
      deployment_timestamp: timestamp()
      autoscaling: {
        minReplicas: var.min_containers,
        maxReplicas: var.min_containers,
        targetCPUUtilizationPercentage: var.autoscaling_target_cpu_percentage
        targetMemoryUtilizationPercentage: var.autoscaling_target_mem_percentage
      },
      port: var.port,
      containerResourceLimits: var.container_resource_limits,
      containerResourceRequests: var.container_resource_requests,
      deployPods: (var.image != "AUTO") || (var.tag != null),
      image: var.image == "AUTO" ? "${aws_ecr_repository.repo[0].repository_url}:${var.tag}" : var.image
      version: var.tag == null ? "latest" : var.tag
      livenessProbePath: var.liveness_probe_path,
      readinessProbePath: var.readiness_probe_path,
      envVars: var.env_vars,
      secrets: var.secrets,
      domain: local.domain,
      pathPrefix: local.path_prefix,
      layerName: var.layer_name,
      moduleName: var.module_name
      iamRoleArn: aws_iam_role.k8s_service.arn
    })
  ]
  atomic          = true
  cleanup_on_fail = true
}

