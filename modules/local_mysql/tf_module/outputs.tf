output "db_user" {
  value = var.db_user
}

output "db_password" {
  value     = var.db_password
  sensitive = true
}

output "db_host" {
  value = "opta-local-mysql.${var.paasns}.svc.cluster.local"
}

output "db_name" {
  value = var.db_name
}