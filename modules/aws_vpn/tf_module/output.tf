output "vpn_dns_name" {
  value = aws_ec2_client_vpn_endpoint.vpn.dns_name
}

output "vpn_ca_cert_parameter_arn" {
  value = aws_ssm_parameter.ca_pem.arn
}

output "vpn_ca_key_parameter_arn" {
  value = aws_ssm_parameter.ca_key.arn
}

output "ovpn_profile_parameter_arn" {
  value = aws_ssm_parameter.ovpn_profile.arn
}