output "vpn_dns_name" {
  value = aws_ec2_client_vpn_endpoint.vpn.dns_name
}

output "vpn_ca_cert" {
  value = tls_self_signed_cert.ca_cert.cert_pem
}

output "vpn_client_cert" {
  value = tls_locally_signed_cert.client_issuer_cert.cert_pem
}

output "vpn_client_key" {
  value = tls_private_key.client_issuer_key.private_key_pem
}

output "ovpn_profile_parameter_arn" {
  value = aws_ssm_parameter.ovpn_profile.arn
}