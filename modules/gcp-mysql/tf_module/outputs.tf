// This list of outputs needs to be the same as the ones for gcp-postgres and should match the ones at gcp_k8s_service.py:handle_rds_link()
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