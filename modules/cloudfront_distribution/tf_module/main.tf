data "aws_s3_bucket" "current_bucket" {
  count  = local.s3_distribution_count
  bucket = var.bucket_name
}

data "aws_s3_bucket" "logging_bucket" {
  count  = var.s3_log_bucket_name == null ? 0 : 1
  bucket = var.s3_log_bucket_name
}

locals {
  lb_distribution_count = var.eks_load_balancer_enabled == true ? 1 : 0
  s3_distribution_count = var.s3_load_balancer_enabled == true ? 1 : 0
}

resource "aws_cloudfront_distribution" "lb_distribution" {
  count = local.lb_distribution_count
  origin {
    domain_name = var.load_balancer
    origin_id   = local.lb_origin_id
    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "http-only"
      origin_ssl_protocols   = ["TLSv1.2", "TLSv1.1", "TLSv1"]
    }
  }

  comment         = "Opta managed cloudfront distribution ${var.layer_name}-${var.module_name}"
  enabled         = true
  is_ipv6_enabled = true

  dynamic "logging_config" {
    for_each = var.s3_log_bucket_name == null ? [] : [1]
    content {
      include_cookies = true
      bucket          = data.aws_s3_bucket.logging_bucket[0].bucket_domain_name
      prefix          = "cloudfront/${var.layer_name}/${var.module_name}"
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD", "OPTIONS"]
    cached_methods         = ["GET", "HEAD", "OPTIONS"]
    target_origin_id       = local.lb_origin_id
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = true
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

resource "aws_cloudfront_distribution" "s3_distribution" {
  count = local.s3_distribution_count
  origin {
    domain_name = data.aws_s3_bucket.current_bucket[0].bucket_regional_domain_name
    origin_id   = local.s3_origin_id

    s3_origin_config {
      origin_access_identity = var.origin_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Opta managed cloudfront distribution ${var.layer_name}-${var.module_name}"
  default_root_object = var.default_page_file

  dynamic "logging_config" {
    for_each = var.s3_log_bucket_name == null ? [] : [1]
    content {
      include_cookies = true
      bucket          = data.aws_s3_bucket.logging_bucket[0].bucket_domain_name
      prefix          = "cloudfront/${var.layer_name}/${var.module_name}"
    }
  }

  dynamic "custom_error_response" {
    for_each = var.status_404_page_file == null ? [] : [1]
    content {
      error_caching_min_ttl = 10
      error_code            = 404
      response_code         = 404
      response_page_path    = var.status_404_page_file
    }
  }

  dynamic "custom_error_response" {
    for_each = var.status_500_page_file == null ? [] : [1]
    content {
      error_caching_min_ttl = 10
      error_code            = 500
      response_code         = 500
      response_page_path    = var.status_500_page_file
    }
  }

  aliases = var.domains

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD", "OPTIONS"]
    target_origin_id = local.s3_origin_id

    forwarded_values {
      query_string = true
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    compress               = true
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }


  price_class = var.price_class

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = var.acm_cert_arn == null ? true : false
    acm_certificate_arn            = var.acm_cert_arn
    ssl_support_method             = "sni-only"
  }
}