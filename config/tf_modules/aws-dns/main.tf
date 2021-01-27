resource "aws_route53_zone" "public" {
  count = var.is_private ? 0 : 1
  name = var.domain_name
}

resource "aws_route53_zone" "private" {
  count = var.is_private ? 1 : 0
  name = var.domain_name
  vpc {
    vpc_id = var.vpc_id
  }
}