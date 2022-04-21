resource "aws_ses_domain_identity" "email" {
  domain = var.domain
}

resource "aws_route53_record" "amazonses_verification_record" {
  zone_id = var.zone_id
  name    = "_amazonses.${aws_ses_domain_identity.email.id}"
  type    = "TXT"
  ttl     = "600"
  records = [aws_ses_domain_identity.email.verification_token]
}

resource "aws_ses_domain_identity_verification" "example_verification" {
  domain = aws_ses_domain_identity.email.id

  depends_on = [aws_route53_record.amazonses_verification_record]
}


### MAIL_FROM setup

resource "aws_ses_domain_mail_from" "email" {
  domain           = aws_ses_domain_identity.email.domain
  mail_from_domain = "${var.mail_from_prefix}.${aws_ses_domain_identity.email.domain}"
}

# Route53 MX record
resource "aws_route53_record" "ses_domain_mail_from_mx" {
  zone_id = var.zone_id
  name    = aws_ses_domain_mail_from.email.mail_from_domain
  type    = "MX"
  ttl     = "600"
  records = ["10 feedback-smtp.${data.aws_region.current.id}.amazonses.com"]
}

# Route53 TXT record for SPF
resource "aws_route53_record" "ses_domain_mail_from_txt" {
  zone_id = var.zone_id
  name    = aws_ses_domain_mail_from.email.mail_from_domain
  type    = "TXT"
  ttl     = "600"
  records = ["v=spf1 include:amazonses.com -all"]
}

### DKIM
resource "aws_ses_domain_dkim" "dkim" {
  domain = aws_ses_domain_identity.email.domain
}

resource "aws_route53_record" "amazonses_dkim_record" {
  count   = 3
  zone_id = var.zone_id
  name    = "${element(aws_ses_domain_dkim.dkim.dkim_tokens, count.index)}._domainkey"
  type    = "CNAME"
  ttl     = "600"
  records = ["${element(aws_ses_domain_dkim.dkim.dkim_tokens, count.index)}.dkim.amazonses.com"]
}

### Blanket sender policy

data "aws_iam_policy_document" "sender" {
  statement {
    sid = "SendEmail"
    #tfsec:ignore:aws-iam-no-policy-wildcards
    actions = ["ses:Send*"]
    #tfsec:ignore:aws-iam-no-policy-wildcards
    resources = ["*"]
    condition {
      test     = "StringLike"
      variable = "ses:FromAddress"
      values   = ["*@${var.domain}"]
    }
  }
}

resource "aws_iam_policy" "sender" {
  name   = "${var.env_name}-${var.layer_name}-${var.module_name}-sender"
  policy = data.aws_iam_policy_document.sender.json
}
