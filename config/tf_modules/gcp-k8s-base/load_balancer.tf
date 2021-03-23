resource "google_compute_global_address" "load_balancer" {
  name    = "opta-${var.layer_name}"
}

resource "google_compute_http_health_check" "healthcheck" {
  name               = "opta-${var.layer_name}"
}

data "google_compute_network_endpoint_group" "http" {
  name = "opta-${var.layer_name}-http"
  depends_on = [
    helm_release.ingress-nginx
  ]
}


data "google_compute_network_endpoint_group" "https" {
  name = "opta-${var.layer_name}-https"
  depends_on = [
    helm_release.ingress-nginx
  ]
}

resource "google_compute_backend_service" "backend_service" {
  name        = "opta-${var.layer_name}"
  port_name   = "http"
  protocol    = "HTTP"

  health_checks = [google_compute_http_health_check.healthcheck.id]

  dynamic "backend" {
    for_each = var.delegated ? [data.google_compute_network_endpoint_group.http.id, data.google_compute_network_endpoint_group.https.id] : [data.google_compute_network_endpoint_group.http.id]
    content {
      group = backend.value
    }
  }
  depends_on = [helm_release.ingress-nginx]
}

resource "google_compute_url_map" "http" {
  name        = "opta-${var.layer_name}"
  default_service = google_compute_backend_service.backend_service.id
  dynamic "default_url_redirect" {
    for_each = var.delegated ? [1] : []
    content {
      redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"  // 301 redirect
      strip_query            = false
      https_redirect         = true  // this is the magic
    }
  }
}

resource "google_compute_url_map" "https" {
  name        = "opta-${var.layer_name}"
  default_service = google_compute_backend_service.backend_service.id
}


resource "google_compute_target_http_proxy" "proxy" {
  name = "opta-${var.layer_name}"
  url_map = google_compute_url_map.http.name
}

resource "google_compute_target_https_proxy" "proxy" {
  count            = var.delegated ? 1 : 0
  name             = "opta-${var.layer_name}"
  url_map          = google_compute_url_map.https.name
  ssl_certificates = [data.google_compute_ssl_certificate.certificate[0].self_link]
}

resource "google_compute_global_forwarding_rule" "http" {
  name       = "opta-${var.layer_name}-http"
  target     = google_compute_target_http_proxy.proxy.self_link
  ip_address = google_compute_global_address.load_balancer.address
  port_range = "80"
}

resource "google_compute_global_forwarding_rule" "https" {
  count      = var.delegated ? 1 : 0
  name       = "opta-${var.layer_name}-https"
  target     = google_compute_target_https_proxy.proxy[0].self_link
  ip_address = google_compute_global_address.load_balancer.address
  port_range = "443"
}

resource "google_dns_record_set" "default" {
  name         = var.domain
  type         = "A"
  ttl          = 3600
  managed_zone = data.google_dns_managed_zone.public.name
  rrdatas      = [google_compute_global_address.load_balancer.address]
}

resource "google_dns_record_set" "wildcard" {
  name         = "*.${var.domain}"
  type         = "A"
  ttl          = 3600
  managed_zone = data.google_dns_managed_zone.public.name
  rrdatas      = [google_compute_global_address.load_balancer.address]
}

data "google_dns_managed_zone" "public" {
  name = "opta-${var.layer_name}"
}

data "google_compute_ssl_certificate" "certificate" {
  count = var.delegated? 1 : 0
  name = "opta-${var.env_name}"
}