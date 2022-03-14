# For linkerd you need to provide the cert for mTLS
# https://gist.github.com/DevOpsFu/15f5ac8b703ee0708083444d7a6a3b3b
resource "tls_private_key" "trustanchor_key" {
  algorithm   = "ECDSA"
  ecdsa_curve = "P256"
}

resource "tls_self_signed_cert" "trustanchor_cert" {
  key_algorithm         = tls_private_key.trustanchor_key.algorithm
  private_key_pem       = tls_private_key.trustanchor_key.private_key_pem
  validity_period_hours = 87600
  is_ca_certificate     = true

  subject {
    common_name = "identity.linkerd.cluster.local"
  }

  allowed_uses = [
    "crl_signing",
    "cert_signing",
    "server_auth",
    "client_auth"
  ]
}

resource "tls_private_key" "issuer_key" {
  algorithm   = "ECDSA"
  ecdsa_curve = "P256"
}

resource "tls_cert_request" "issuer_req" {
  key_algorithm   = tls_private_key.issuer_key.algorithm
  private_key_pem = tls_private_key.issuer_key.private_key_pem

  subject {
    common_name = "identity.linkerd.cluster.local"
  }
}

resource "tls_locally_signed_cert" "issuer_cert" {
  cert_request_pem      = tls_cert_request.issuer_req.cert_request_pem
  ca_key_algorithm      = tls_private_key.trustanchor_key.algorithm
  ca_private_key_pem    = tls_private_key.trustanchor_key.private_key_pem
  ca_cert_pem           = tls_self_signed_cert.trustanchor_cert.cert_pem
  validity_period_hours = 87600
  is_ca_certificate     = true

  allowed_uses = [
    "crl_signing",
    "cert_signing",
    "server_auth",
    "client_auth"
  ]
}


resource "helm_release" "linkerd" {
  count      = var.linkerd_enabled ? 1 : 0
  chart      = "linkerd2"
  name       = "linkerd"
  repository = "https://helm.linkerd.io/stable"
  version    = "2.10.2" // NOTE: Check https://linkerd.io/2.11/tasks/using-ingress/#nginx whenever we update linkerd

  values = var.linkerd_high_availability ? [
    file("${path.module}/values-ha.yaml"), # Adding the high-availability default values.
    yamlencode({
      podAnnotations : {
        "cluster-autoscaler.kubernetes.io/safe-to-evict" : "true"
      }
      identityTrustAnchorsPEM : tls_self_signed_cert.trustanchor_cert.cert_pem
      identity : {
        issuer : {
          crtExpiry : tls_locally_signed_cert.issuer_cert.validity_end_time
          tls : {
            crtPEM : tls_locally_signed_cert.issuer_cert.cert_pem
            keyPEM : tls_private_key.issuer_key.private_key_pem
          }
        }
      }
    }), yamlencode(var.linkerd_values)
    ] : [yamlencode({
      podAnnotations : {
        "cluster-autoscaler.kubernetes.io/safe-to-evict" : "true"
      }
      identityTrustAnchorsPEM : tls_self_signed_cert.trustanchor_cert.cert_pem
      identity : {
        issuer : {
          crtExpiry : tls_locally_signed_cert.issuer_cert.validity_end_time
          tls : {
            crtPEM : tls_locally_signed_cert.issuer_cert.cert_pem
            keyPEM : tls_private_key.issuer_key.private_key_pem
          }
        }
      }
  }), yamlencode(var.linkerd_values)]
}