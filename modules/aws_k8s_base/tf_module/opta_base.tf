# Reusing CA authority made for linkerd
resource "tls_private_key" "default" {
  algorithm   = "RSA"
#  ecdsa_curve = "P256"
}

resource "tls_cert_request" "default_cert_request" {
  key_algorithm   = tls_private_key.issuer_key.algorithm
  private_key_pem = tls_private_key.issuer_key.private_key_pem
  dns_names = ["*.elb.${data.aws_region.current.name}.amazonaws.com"]

  subject {
    common_name = "*.elb.${data.aws_region.current.name}.amazonaws.com"
    organization = "Org"
  }
}

resource "tls_locally_signed_cert" "default_cert" {
  cert_request_pem      = tls_cert_request.default_cert_request.cert_request_pem
  ca_key_algorithm      = tls_private_key.trustanchor_key.algorithm
  ca_private_key_pem    = tls_private_key.trustanchor_key.private_key_pem
  ca_cert_pem           = tls_self_signed_cert.trustanchor_cert.cert_pem
  validity_period_hours = 87600

  allowed_uses = [
    "crl_signing",
    "cert_signing",
    "server_auth",
    "client_auth"
  ]
}

resource "helm_release" "opta_base" {
  chart     = "${path.module}/opta-base"
  name      = "opta-base"
  namespace = "default"
  values = [
    yamlencode({
      adminArns : var.admin_arns
#      tls_key : base64encode(var.private_key),
#      tls_crt : base64encode(join("\n", [var.certificate_body, var.certificate_chain])),
      tls_key : base64encode(tls_private_key.default.private_key_pem),
      tls_crt : base64encode(tls_locally_signed_cert.default_cert.cert_pem)
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