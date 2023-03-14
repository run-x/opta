resource "helm_release" "nvidia_driver_installer" {
  chart           = "${path.module}/nvidia-driver-installer"
  name            = "nvidia-driver-installer"
  namespace       = "kube-system"
  atomic          = true
  cleanup_on_fail = true
  values = [
    yamlencode({
      use_latest_version : var.nvidia_gpu_driver_version == "LATEST"
    })
  ]
}
