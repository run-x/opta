# Following example https://registry.terraform.io/providers/hashicorp/aws/latest/docs/guides/version-3-upgrade#resource-aws_acm_certificate
# which should have addressed the issue https://github.com/terraform-providers/terraform-provider-aws/issues/8531
resource "aws_acm_certificate" "certificate" {
  count                     = var.delegated ? 1 : 0
  domain_name               = aws_route53_zone.public.name
  subject_alternative_names = ["*.${aws_route53_zone.public.name}"]
  validation_method         = "DNS"
  tags = {
    Name = "opta-${var.env_name}"
  }
}

resource "aws_route53_record" "validation_record" {
  for_each = {
    for dvo in(var.delegated ? aws_acm_certificate.certificate[0].domain_validation_options : []) : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }
  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.public.id
}

resource "aws_acm_certificate_validation" "example_com" {
  count                   = var.delegated ? 1 : 0
  certificate_arn         = aws_acm_certificate.certificate[0].arn
  validation_record_fqdns = [for record in aws_route53_record.validation_record : record.fqdn]
}

resource "aws_acm_certificate" "imported_certificate" {
  count             = var.upload_cert ? 1 : 0
  private_key       = data.aws_ssm_parameter.private_key[0].value
  certificate_body  = data.aws_ssm_parameter.certificate_body[0].value
  certificate_chain = var.cert_chain_included ? data.aws_ssm_parameter.certificate_chain[0].value : null
  tags = {
    Name = "opta-${var.env_name}"
  }
}
