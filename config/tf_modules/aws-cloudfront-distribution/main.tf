resource "random_string" "default-suffix" {
  length  = 7
  special = false
}

data "aws_s3_bucket" "current_bucket" {
  bucket = var.bucket_name
}

resource "aws_s3_bucket_object" "default_page" {
  bucket       = data.aws_s3_bucket.current_bucket.id
  key          = "opta-default-page-${random_string.default-suffix.result}.html"
  source       = "${path.module}/default.html"
  content_type = "text/html"
}

resource "aws_cloudfront_distribution" "s3_distribution" {
  origin {
    domain_name = data.aws_s3_bucket.current_bucket.bucket_regional_domain_name
    origin_id   = local.s3_origin_id

    s3_origin_config {
      origin_access_identity = var.origin_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Opta managed cloudfront distribution ${var.layer_name}-${var.module_name}"
  default_root_object = var.default_page_file == null ? aws_s3_bucket_object.default_page.key : var.default_page_file

  dynamic "logging_config" {
    for_each = var.s3_log_bucket_name == null ? [] : [1]
    content {
      include_cookies = true
      bucket          = var.s3_log_bucket_name
      prefix          = "cloudfront/${var.layer_name}/${var.module_name}"
    }
  }

  custom_error_response {
    error_caching_min_ttl = 10
    error_code            = 404
    response_code         = 404
    response_page_path    = var.status_404_page_file == null ? "/${aws_s3_bucket_object.default_page.key}" : var.status_404_page_file
  }

  custom_error_response {
    error_caching_min_ttl = 10
    error_code            = 500
    response_code         = 500
    response_page_path    = var.status_500_page_file == null ? "/${aws_s3_bucket_object.default_page.key}" : var.status_500_page_file
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