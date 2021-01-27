output "db_user" {
  value = google_sql_user.main-user.name
}

output "db_password" {
  value = google_sql_user.main-user.password
  sensitive = true
}

output "db_host" {
  value = google_sql_database_instance.main.first_ip_address
}

output "db_name" {
  value = google_sql_database.main.name
}
