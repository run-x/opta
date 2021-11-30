resource "aws_route53_zone" "public" {
  name = var.domain
  tags = {
    Name               = "opta-${var.env_name}"
    "opta-environment" = var.env_name
  }
  force_destroy = true
}