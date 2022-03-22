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
  dns_names       = ["optaisawesome.com"]
  ip_addresses    = ["${google_compute_global_address.load_balancer.address}"]

  subject {
    common_name  = "optaisawesome.com"
    organization = "Org"
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
      tls_crt : var.private_key == "" && var.expose_self_signed_ssl ? base64encode(tls_locally_signed_cert.default_cert[0].cert_pem) : base64encode(join("\n", [var.certificate_body, var.certificate_chain]))
      tls_key : var.private_key == "" && var.expose_self_signed_ssl ? base64encode(tls_private_key.default[0].private_key_pem) : base64encode(var.private_key),
    })
  ]
}