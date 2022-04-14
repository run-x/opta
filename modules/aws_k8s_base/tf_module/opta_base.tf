resource "tls_private_key" "nginx_ca" {
  count     = var.expose_self_signed_ssl ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = "2048"
}

resource "tls_self_signed_cert" "nginx_ca" {
  count             = var.expose_self_signed_ssl ? 1 : 0
  key_algorithm     = "RSA"
  private_key_pem   = tls_private_key.nginx_ca[0].private_key_pem
  is_ca_certificate = true

  subject {
    common_name         = "Opta is awesome"
    organization        = "Opta Self Signed"
    organizational_unit = "opta"
    street_address      = []
  }

  validity_period_hours = 87600

  allowed_uses = [
    "digital_signature",
    "cert_signing",
    "crl_signing",
  ]
}
resource "tls_private_key" "default" {
  count     = var.expose_self_signed_ssl ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = "2048"
}

resource "tls_cert_request" "default_cert_request" {
  count           = var.expose_self_signed_ssl ? 1 : 0
  key_algorithm   = tls_private_key.default[0].algorithm
  private_key_pem = tls_private_key.default[0].private_key_pem
  dns_names       = ["*.elb.${data.aws_region.current.name}.amazonaws.com"]

  subject {
    common_name    = "*.elb.${data.aws_region.current.name}.amazonaws.com"
    organization   = "Org"
    street_address = []
  }

  lifecycle {
    ignore_changes = [
      id
    ]
  }
}

resource "tls_locally_signed_cert" "default_cert" {
  count                 = var.expose_self_signed_ssl ? 1 : 0
  cert_request_pem      = tls_cert_request.default_cert_request[0].cert_request_pem
  ca_key_algorithm      = tls_private_key.nginx_ca[0].algorithm
  ca_private_key_pem    = tls_private_key.nginx_ca[0].private_key_pem
  ca_cert_pem           = tls_self_signed_cert.nginx_ca[0].cert_pem
  validity_period_hours = 87600

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
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
      tls_key : var.private_key == "" && var.expose_self_signed_ssl ? base64encode(tls_private_key.default[0].private_key_pem) : base64encode(var.private_key),
      tls_crt : var.private_key == "" && var.expose_self_signed_ssl ? base64encode(tls_locally_signed_cert.default_cert[0].cert_pem) : base64encode(join("\n", [var.certificate_body, var.certificate_chain]))
    })
  ]
  depends_on = [
    time_sleep.wait_a_bit
  ]
}

resource "time_sleep" "wait_a_bit" {
  depends_on = [
    helm_release.autoscaler,
    helm_release.load_balancer
  ]

  create_duration = "30s"
}