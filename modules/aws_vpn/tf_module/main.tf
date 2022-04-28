data "aws_vpc" "vpc" {
  id = var.vpc_id
}

data "aws_kms_key" "env_key" {
  key_id = var.kms_account_key_arn
}

data "aws_security_group" "vpn" {
  id = var.vpn_sg_id
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
  #  server_certificate_arn = "arn:aws:acm:us-east-1:445935066876:certificate/877f3c93-61bc-4b19-90c3-137b1e6f24bc"
  client_cidr_block  = var.client_cidr_block
  vpc_id             = var.vpc_id
  security_group_ids = [data.aws_security_group.vpn.id]
  split_tunnel       = true

  authentication_options {
    type                       = "certificate-authentication"
    root_certificate_chain_arn = aws_acm_certificate.client.arn
    #    root_certificate_chain_arn = "arn:aws:acm:us-east-1:445935066876:certificate/f552e3da-0c41-407b-8108-da2c8053930f"
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