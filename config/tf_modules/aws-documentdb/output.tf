output "db_host" {
  value = aws_docdb_cluster.cluster.endpoint
}

output "db_user" {
  value = aws_docdb_cluster.cluster.master_username
}

output "db_password" {
  value     = aws_docdb_cluster.cluster.master_password
  sensitive = true
}