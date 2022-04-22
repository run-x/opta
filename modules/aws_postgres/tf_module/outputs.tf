resource "time_sleep" "wait_for_db" {
  create_duration = "1s"

  triggers = {
    # This sets up a proper dependency on the RAM association
    primary   = var.existing_global_database_id == null ? aws_rds_cluster_instance.db_instance[0].id : ""
    secondary = var.existing_global_database_id == null ? "" : aws_rds_cluster_instance.secondary[0].id
  }
}

output "db_user" {
  value      = (var.existing_global_database_id == null && var.restore_from_snapshot == null) ? aws_rds_cluster.db_cluster[0].master_username : (var.restore_from_snapshot == null ? "UNKNOWN_SEE_PRIMARY_DB" : "UNKNOWN_SEE_ORIGINAL_DB")
  depends_on = [time_sleep.wait_for_db]
}

output "db_password" {
  value      = (var.existing_global_database_id == null && var.restore_from_snapshot == null) ? aws_rds_cluster.db_cluster[0].master_password : (var.restore_from_snapshot == null ? "UNKNOWN_SEE_PRIMARY_DB" : "UNKNOWN_SEE_ORIGINAL_DB")
  sensitive  = true
  depends_on = [time_sleep.wait_for_db]
}

output "db_host" {
  value      = var.existing_global_database_id == null ? aws_rds_cluster.db_cluster[0].endpoint : aws_rds_cluster.secondary[0].reader_endpoint
  depends_on = [time_sleep.wait_for_db]
}

output "db_name" {
  value      = (var.existing_global_database_id == null && var.restore_from_snapshot == null) ? aws_rds_cluster.db_cluster[0].database_name : (var.restore_from_snapshot == null ? "UNKNOWN_SEE_PRIMARY_DB" : "UNKNOWN_SEE_ORIGINAL_DB")
  depends_on = [time_sleep.wait_for_db]
}


output "global_database_id" {
  value = var.create_global_database ? aws_rds_global_cluster.global_cluster[0].id : "N/A"
}
