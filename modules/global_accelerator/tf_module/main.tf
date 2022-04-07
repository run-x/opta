resource "aws_globalaccelerator_accelerator" "accelerator" {
  name            = "Example"
  ip_address_type = "IPV4"
  enabled         = true

  attributes {
    flow_logs_enabled   = var.flow_logs_enabled
    flow_logs_s3_bucket = var.flow_logs_bucket
    flow_logs_s3_prefix = var.flow_logs_prefix
  }
}

resource "aws_globalaccelerator_listener" "http" {
  accelerator_arn = aws_globalaccelerator_accelerator.accelerator.id
  client_affinity = "NONE"
  protocol        = "TCP"

  port_range {
    from_port = 80
    to_port   = 80
  }

  port_range {
    from_port = 443
    to_port   = 443
  }
}

resource "aws_globalaccelerator_endpoint_group" "endpoint" {
  listener_arn = aws_globalaccelerator_listener.http.id

  endpoint_configuration {
    endpoint_id = var.endpoint_id
    weight      = 100
  }
}

resource "aws_route53_record" "domain" {
  count           = var.domain == "" ? 0 : 1
  name            = var.domain
  type            = "A"
  zone_id         = var.zone_id
  allow_overwrite = true
  alias {
    evaluate_target_health = false
    name                   = aws_globalaccelerator_accelerator.accelerator.dns_name
    zone_id                = aws_globalaccelerator_accelerator.accelerator.hosted_zone_id
  }
}

resource "aws_route53_record" "sub_domain" {
  count           = var.domain == "" ? 0 : 1
  name            = "*.${var.domain}"
  type            = "A"
  zone_id         = var.zone_id
  allow_overwrite = true
  alias {
    evaluate_target_health = false
    name                   = aws_globalaccelerator_accelerator.accelerator.dns_name
    zone_id                = aws_globalaccelerator_accelerator.accelerator.hosted_zone_id
  }
}
