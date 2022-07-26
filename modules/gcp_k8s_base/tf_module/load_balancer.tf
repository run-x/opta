resource "google_compute_ssl_certificate" "external" {
  count       = var.nginx_enabled && var.private_key != "" ? 1 : 0
  name        = "opta-${var.layer_name}"
  certificate = join("\n", [var.certificate_body, var.certificate_chain])
  private_key = var.private_key
}

resource "google_compute_ssl_certificate" "default" {
  count       = var.nginx_enabled && var.expose_self_signed_ssl ? 1 : 0
  name        = "opta-${var.layer_name}-default"
  certificate = tls_locally_signed_cert.default_cert[0].cert_pem
  private_key = tls_private_key.default[0].private_key_pem
}

resource "google_compute_global_address" "load_balancer" {
  count = var.nginx_enabled ? 1 : 0
  name  = "opta-${var.layer_name}"
}

resource "google_compute_health_check" "healthcheck" {
  count = var.nginx_enabled ? 1 : 0
  name  = "opta-${var.layer_name}"
  https_health_check {
    port_specification = "USE_SERVING_PORT"
    request_path       = "/healthz"
  }
}

resource "google_compute_ssl_policy" "policy" {
  count           = var.nginx_enabled ? 1 : 0
  name            = "opta-${var.layer_name}"
  profile         = "MODERN"
  min_tls_version = "TLS_1_2"
}

resource "google_compute_backend_service" "backend_service" {
  count     = var.nginx_enabled ? 1 : 0
  name      = "opta-${var.layer_name}"
  port_name = "https"
  protocol  = "HTTP2"

  health_checks = [google_compute_health_check.healthcheck[0].id]

  dynamic "backend" {
    for_each = local.negs
    content {
      balancing_mode        = "RATE"
      max_rate_per_endpoint = 50
      group                 = backend.value
    }
  }
  depends_on = [helm_release.ingress-nginx, google_compute_health_check.healthcheck]
}

resource "google_compute_url_map" "http" {
  count           = var.nginx_enabled ? 1 : 0
  name            = "opta-${var.layer_name}"
  default_service = var.delegated || var.private_key != "" ? null : google_compute_backend_service.backend_service[0].id
  dynamic "default_url_redirect" {
    for_each = var.delegated || var.private_key != "" ? [1] : []
    content {
      redirect_response_code = "MOVED_PERMANENTLY_DEFAULT" // 301 redirect
      strip_query            = false
      https_redirect         = true // this is the magic
    }
  }
}

resource "google_compute_url_map" "https" {
  count           = var.nginx_enabled && (var.delegated || var.private_key != "" || var.expose_self_signed_ssl) ? 1 : 0
  name            = "opta-${var.layer_name}-https"
  default_service = google_compute_backend_service.backend_service[0].id
}


resource "google_compute_target_http_proxy" "proxy" {
  count   = var.nginx_enabled ? 1 : 0
  name    = "opta-${var.layer_name}"
  url_map = google_compute_url_map.http[0].name
}

resource "google_compute_target_https_proxy" "proxy" {
  count            = var.nginx_enabled && (var.delegated || var.private_key != "" || var.expose_self_signed_ssl) ? 1 : 0
  name             = "opta-${var.layer_name}"
  url_map          = google_compute_url_map.https[0].name
  ssl_certificates = var.delegated ? [var.cert_self_link] : (var.private_key != "" ? [google_compute_ssl_certificate.external[0].self_link] : [google_compute_ssl_certificate.default[0].self_link])
  ssl_policy       = google_compute_ssl_policy.policy[0].self_link
}

resource "google_compute_global_forwarding_rule" "http" {
  count      = var.nginx_enabled ? 1 : 0
  name       = "opta-${var.layer_name}-http"
  target     = google_compute_target_http_proxy.proxy[0].self_link
  ip_address = google_compute_global_address.load_balancer[0].address
  port_range = "80"
}

resource "google_compute_global_forwarding_rule" "https" {
  count      = var.nginx_enabled && (var.delegated || var.private_key != "" || var.expose_self_signed_ssl) ? 1 : 0
  name       = "opta-${var.layer_name}-https"
  target     = google_compute_target_https_proxy.proxy[0].self_link
  ip_address = google_compute_global_address.load_balancer[0].address
  port_range = "443"
}

resource "google_dns_record_set" "default" {
  count        = var.nginx_enabled && var.hosted_zone_name != "" ? 1 : 0
  name         = "${var.domain}."
  type         = "A"
  ttl          = 3600
  managed_zone = var.hosted_zone_name
  rrdatas      = [google_compute_global_address.load_balancer[0].address]
}

resource "google_dns_record_set" "wildcard" {
  count        = var.nginx_enabled && var.hosted_zone_name != "" ? 1 : 0
  name         = "*.${var.domain}."
  type         = "A"
  ttl          = 3600
  managed_zone = var.hosted_zone_name
  rrdatas      = [google_compute_global_address.load_balancer[0].address]
}
