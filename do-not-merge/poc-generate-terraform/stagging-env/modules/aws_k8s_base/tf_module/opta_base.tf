resource "helm_release" "opta_base" {
  chart     = "${path.module}/opta-base"
  name      = "opta-base"
  namespace = "default"
  values = [
    yamlencode({
      adminArns : var.admin_arns
      tls_key : base64encode(var.private_key),
      tls_crt : base64encode(join("\n", [var.certificate_body, var.certificate_chain]))
    })
  ]
  depends_on = [
    time_sleep.wait_a_bit
  ]
}

resource "time_sleep" "wait_a_bit" {
  depends_on = [
    helm_release.cert_manager,
    helm_release.autoscaler,
    helm_release.load_balancer,
    helm_release.external-dns
  ]

  create_duration = "30s"
}