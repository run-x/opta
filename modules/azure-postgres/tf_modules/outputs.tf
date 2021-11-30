output "db_user" {
  value = "${azurerm_postgresql_server.opta.administrator_login}@${azurerm_postgresql_server.opta.name}"
}

output "db_password" {
  value     = azurerm_postgresql_server.opta.administrator_login_password
  sensitive = true
}

output "db_host" {
  value = azurerm_private_endpoint.opta.private_service_connection[0].private_ip_address
}

output "db_name" {
  value = azurerm_postgresql_database.opta.name
}
