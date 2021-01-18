output "db_user" {
  value = aws_rds_cluster.db_cluster.master_username
}

output "db_password" {
  value = aws_rds_cluster.db_cluster.master_password
  sensitive = true
}

output "db_host" {
  value = aws_rds_cluster_instance.db_instance[0].endpoint
}

output "db_name" {
  value = aws_rds_cluster.db_cluster.database_name
}