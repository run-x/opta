resource "helm_release" "nvidia_daemonset" {
  chart           = "nvidia-device-plugin"
  name            = "nvidia-device-plugin"
  repository      = "https://nvidia.github.io/k8s-device-plugin"
  version         = "0.9.0"
  atomic          = true
  cleanup_on_fail = true
  values = [
    yamlencode({
      nodeSelector : {
        gpu : "true"
      }
    })
  ]
}