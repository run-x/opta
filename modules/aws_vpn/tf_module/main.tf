data "aws_vpc" "vpc" {
  id = var.vpc_id
}

data "aws_kms_key" "env_key" {
  key_id = var.kms_account_key_arn
}

resource "aws_security_group" "vpn" {
  name_prefix = "opta-${var.env_name}-vpn"
  description = "VPN security group."
  vpc_id      = var.vpc_id

  tags = {
    "Name" = "opta-${var.env_name}-vpn"
  }

  egress {
    description = "alloutbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = [data.aws_vpc.vpc.cidr_block]
  }
}

resource "random_id" "vpn_log_suffix" {
  byte_length = 8
}

resource "aws_cloudwatch_log_group" "vpn_logs" {
  name              = "opta-${var.env_name}-vpn-${random_id.vpn_log_suffix.hex}"
  kms_key_id        = data.aws_kms_key.env_key.arn
  retention_in_days = "14"
  lifecycle { ignore_changes = [name] }
}

resource "aws_cloudwatch_log_stream" "logs" {
  log_group_name = aws_cloudwatch_log_group.vpn_logs.name
  name           = "logs"
}

resource "aws_ec2_client_vpn_endpoint" "vpn" {
  description            = "opta-${var.env_name}-${var.module_name}"
  server_certificate_arn = aws_acm_certificate.server.arn
  client_cidr_block      = var.client_cidr_block
  vpc_id                 = var.vpc_id
  security_group_ids     = [aws_security_group.vpn.id]
  split_tunnel           = true

  authentication_options {
    type                       = "certificate-authentication"
    root_certificate_chain_arn = aws_acm_certificate.server.arn
  }

  connection_log_options {
    enabled               = true
    cloudwatch_log_group  = aws_cloudwatch_log_group.vpn_logs.name
    cloudwatch_log_stream = aws_cloudwatch_log_stream.logs.name
  }
}

resource "aws_ec2_client_vpn_network_association" "association" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.vpn.id
  subnet_id              = var.public_subnets_ids[0]
}

resource "aws_ec2_client_vpn_authorization_rule" "example" {
  client_vpn_endpoint_id = aws_ec2_client_vpn_endpoint.vpn.id
  target_network_cidr    = data.aws_vpc.vpc.cidr_block
  authorize_all_groups   = true
}