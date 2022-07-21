output "load_balancer_raw_ip" {
  value = azurerm_public_ip.opta[0].ip_address
}