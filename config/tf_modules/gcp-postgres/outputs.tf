output "db_user" {
  value = google_sql_user.root.name
}

output "db_password" {
  value     = google_sql_user.root.password
  sensitive = true
}

output "db_host" {
  value = google_sql_database_instance.instance.private_ip_address
}

output "db_name" {
  value = google_sql_database_instance.instance.name
}