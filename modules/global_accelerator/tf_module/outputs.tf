output "global_accelerator_arn" {
  value = aws_globalaccelerator_accelerator.accelerator.id
}


output "global_accelerator_dns_name" {
  value = aws_globalaccelerator_accelerator.accelerator.dns_name
}

output "global_accelerator_ip_addresses" {
  value = aws_globalaccelerator_accelerator.accelerator.ip_sets[0].ip_addresses
}

output "global_accelerator_endpoint_arns" {
  value = aws_globalaccelerator_endpoint_group.endpoint[*].arn
}