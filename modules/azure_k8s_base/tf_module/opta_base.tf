resource "helm_release" "opta_base" {
  chart     = "${path.module}/opta-base"
  name      = "opta-base"
  namespace = "default"
  values = [yamlencode({
    tls_key : base64encode(var.private_key),
    tls_crt : base64encode(join("\n", [var.certificate_body, var.certificate_chain])),
    nginxEnabled : var.nginx_enabled
  })]
}