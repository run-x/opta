resource "tls_private_key" "ca_key" {
  algorithm = "RSA"
  rsa_bits  = "2048"
}

resource "tls_self_signed_cert" "ca_cert" {
  private_key_pem = tls_private_key.ca_key.private_key_pem
  key_algorithm   = "RSA"
  subject {
    organization = "RunX"
  }
  validity_period_hours = 87600
  allowed_uses = [
    "cert_signing",
    "crl_signing"
  ]
  is_ca_certificate = true

}

resource "aws_ssm_parameter" "ca_pem" {
  name        = "/opta/${var.env_name}/vpn-ca-cert-pem"
  description = "The pem of the VPN CA certificate"
  type        = "SecureString"
  tier        = "Advanced"
  value       = tls_self_signed_cert.ca_cert.cert_pem
}

resource "aws_ssm_parameter" "ca_key" {
  name        = "/opta/${var.env_name}/vpn-ca-key-pem"
  description = "The pem of the key of the VPN CA certificate"
  type        = "SecureString"
  tier        = "Advanced"
  value       = tls_private_key.ca_key.private_key_pem
}

resource "tls_private_key" "server_key" {
  algorithm = "RSA"
  rsa_bits  = "2048"
}

resource "tls_cert_request" "server_req" {
  key_algorithm   = tls_private_key.server_key.algorithm
  private_key_pem = tls_private_key.server_key.private_key_pem
  dns_names       = ["server"]

  subject {
    common_name = "server"
  }
}

resource "tls_locally_signed_cert" "server_cert" {
  cert_request_pem      = tls_cert_request.server_req.cert_request_pem
  ca_key_algorithm      = tls_private_key.ca_key.algorithm
  ca_private_key_pem    = tls_private_key.ca_key.private_key_pem
  ca_cert_pem           = tls_self_signed_cert.ca_cert.cert_pem
  validity_period_hours = 87600

  allowed_uses = [
    "crl_signing",
    "cert_signing",
    "server_auth",
    "client_auth",
    "key_encipherment",
    "digital_signature",
  ]
}

resource "aws_acm_certificate" "server" {
  private_key       = tls_private_key.server_key.private_key_pem
  certificate_body  = tls_locally_signed_cert.server_cert.cert_pem
  certificate_chain = tls_self_signed_cert.ca_cert.cert_pem
}

resource "tls_private_key" "client_issuer_key" {
  algorithm = "RSA"
  rsa_bits  = "2048"
}

resource "tls_cert_request" "client_issuer_req" {
  key_algorithm   = tls_private_key.client_issuer_key.algorithm
  private_key_pem = tls_private_key.client_issuer_key.private_key_pem

  subject {
    common_name = "client1.domain.tld"
  }
}

resource "tls_locally_signed_cert" "client_issuer_cert" {
  cert_request_pem      = tls_cert_request.client_issuer_req.cert_request_pem
  ca_key_algorithm      = tls_private_key.ca_key.algorithm
  ca_private_key_pem    = tls_private_key.ca_key.private_key_pem
  ca_cert_pem           = tls_self_signed_cert.ca_cert.cert_pem
  validity_period_hours = 87600
  is_ca_certificate     = true

  allowed_uses = [
    "crl_signing",
    "cert_signing",
    "server_auth",
    "client_auth",
    "key_encipherment",
    "digital_signature",
  ]
}


resource "aws_ssm_parameter" "ovpn_profile" {
  name        = "/opta/${var.env_name}/ovpn"
  description = "The vpn profile for the Opta-provisioned AWS VPN endpoint for this environment"
  type        = "SecureString"
  tier        = "Advanced"
  value       = <<EOT
client
dev tun
proto udp
remote opta.${trimprefix(aws_ec2_client_vpn_endpoint.vpn.dns_name, "*.")} 443
remote-random-hostname
resolv-retry infinite
nobind
remote-cert-tls server
cipher AES-256-GCM
verb 3
<ca>
${trim(tls_self_signed_cert.ca_cert.cert_pem, "\n")}
</ca>

reneg-sec 0
<cert>
${trim(tls_locally_signed_cert.client_issuer_cert.cert_pem, "\n")}
</cert>

<key>
${trim(tls_private_key.client_issuer_key.private_key_pem, "\n")}
</key>
EOT
}
