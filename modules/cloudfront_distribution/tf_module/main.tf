data "aws_s3_bucket" "current_bucket" {
  count  = var.s3_load_balancer_enabled ? 1 : 0
  bucket = var.bucket_name
}

data "aws_s3_bucket" "logging_bucket" {
  count  = var.s3_log_bucket_name == "" ? 0 : 1
  bucket = var.s3_log_bucket_name
}

data "aws_lb" "ingress-nginx" {
  count = var.eks_load_balancer_enabled ? 1 : 0
  arn   = var.load_balancer_arn
}


# This is optional, see Opta docs for this here: https://docs.opta.dev/reference/aws/modules/cloudfront-distribution/
#tfsec:ignore:aws-cloudfront-enable-waf
resource "aws_cloudfront_distribution" "distribution" {

  comment         = "Opta managed cloudfront distribution ${var.layer_name}-${var.module_name}"
  enabled         = true
  is_ipv6_enabled = true
  price_class     = var.price_class
  aliases         = var.acm_cert_arn == "" ? [] : concat(var.domains, formatlist("*.%s", var.domains))
  web_acl_id      = var.web_acl_id

  dynamic "logging_config" {
    for_each = var.s3_log_bucket_name == null ? [] : [1]
    content {
      include_cookies = true
      bucket          = data.aws_s3_bucket.logging_bucket[0].bucket_domain_name
      prefix          = "cloudfront/${var.layer_name}/${var.module_name}"
    }
  }

  default_root_object = var.s3_load_balancer_enabled == true ? var.default_page_file : null

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }
  # Ignored this because https://github.com/run-x/opta/pull/841#issuecomment-1102915968
  #tfsec:ignore:aws-cloudfront-use-secure-tls-policy
  viewer_certificate {
    cloudfront_default_certificate = var.acm_cert_arn == "" ? true : false
    acm_certificate_arn            = var.acm_cert_arn
    ssl_support_method             = "sni-only"
  }

  dynamic "origin" {
    for_each = var.eks_load_balancer_enabled == true ? [1] : []
    content {
      domain_name = data.aws_lb.ingress-nginx[0].dns_name
      origin_id   = local.lb_origin_id
      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "http-only"
        origin_ssl_protocols   = ["TLSv1.2", "TLSv1.1", "TLSv1"]
      }
    }
  }

  dynamic "origin" {
    for_each = var.s3_load_balancer_enabled == true ? [1] : []
    content {
      domain_name = data.aws_s3_bucket.current_bucket[0].bucket_regional_domain_name
      origin_id   = local.s3_origin_id

      s3_origin_config {
        origin_access_identity = var.origin_access_identity_path
      }
    }
  }

  default_cache_behavior {
    allowed_methods        = var.allowed_methods
    cached_methods         = var.cached_methods
    target_origin_id       = var.load_balancer_arn == "" ? local.s3_origin_id : local.lb_origin_id
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = concat(["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method", "Host"], var.extra_headers)
      cookies {
        forward = "all"
      }
    }
  }

  dynamic "custom_error_response" {
    for_each = var.status_404_page_file == null || var.s3_load_balancer_enabled == false ? [] : [1]
    content {
      error_caching_min_ttl = 10
      error_code            = 404
      response_code         = 404
      response_page_path    = var.status_404_page_file
    }
  }

  dynamic "custom_error_response" {
    for_each = var.status_500_page_file == null || var.s3_load_balancer_enabled == false ? [] : [1]
    content {
      error_caching_min_ttl = 10
      error_code            = 500
      response_code         = 500
      response_page_path    = var.status_500_page_file
    }
  }
}

resource "aws_route53_record" "domain" {
  count           = length(var.domains)
  name            = var.domains[count.index]
  type            = "A"
  zone_id         = var.zone_id
  allow_overwrite = true
  alias {
    name                   = aws_cloudfront_distribution.distribution.domain_name
    zone_id                = aws_cloudfront_distribution.distribution.hosted_zone_id
    evaluate_target_health = true
  }
}

resource "aws_route53_record" "sub_domain" {
  count           = length(var.domains)
  name            = "*.${var.domains[count.index]}"
  type            = "A"
  zone_id         = var.zone_id
  allow_overwrite = true
  alias {
    name                   = aws_cloudfront_distribution.distribution.domain_name
    zone_id                = aws_cloudfront_distribution.distribution.hosted_zone_id
    evaluate_target_health = true
  }
}
