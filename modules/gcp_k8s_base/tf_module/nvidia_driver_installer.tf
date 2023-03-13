resource "helm_release" "nvidia_driver_installer" {
  chart     = "${path.module}/nvidia-driver-installer"
  name      = "nvidia-driver-installer"
  namespace = "kube-system"
  values = [
    yamlencode({
      use_latest_version : var.use_latest_nvidia_gpu_driver
    })
  ]
}
