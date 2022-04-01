resource "aws_rds_global_cluster" "global_cluster" {
  count                        = var.create_global_database ? 1 : 0
  force_destroy                = true
  global_cluster_identifier    = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  source_db_cluster_identifier = aws_rds_cluster.db_cluster[0].arn
}