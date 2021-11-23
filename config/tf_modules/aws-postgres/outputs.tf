output "db_user" {
  value      = aws_rds_cluster.db_cluster.master_username
  depends_on = [aws_rds_cluster_instance.db_instance[0]]
}

output "db_password" {
  value      = aws_rds_cluster.db_cluster.master_password
  sensitive  = true
  depends_on = [aws_rds_cluster_instance.db_instance[0]]
}

output "db_host" {
  value      = aws_rds_cluster.db_cluster.endpoint
  depends_on = [aws_rds_cluster_instance.db_instance[0]]
}

output "db_name" {
  value      = aws_rds_cluster.db_cluster.database_name
  depends_on = [aws_rds_cluster_instance.db_instance[0]]
}