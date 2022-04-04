resource "aws_rds_cluster" "secondary" {
  count                     = var.existing_global_database_id == null ? 0 : 1
  cluster_identifier        = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  db_subnet_group_name      = "opta-${var.env_name}"
  global_cluster_identifier = var.existing_global_database_id
  engine                    = "aurora-postgresql"
  engine_version            = var.engine_version
  vpc_security_group_ids    = concat([data.aws_security_group.security_group.id], var.extra_security_groups_ids)
  backup_retention_period   = var.backup_retention_days
  apply_immediately         = true
  skip_final_snapshot       = true
  storage_encrypted         = true
  kms_key_id                = data.aws_kms_key.main.arn
  deletion_protection       = var.safety
  lifecycle {
    ignore_changes = [storage_encrypted, kms_key_id, cluster_identifier]
  }
}

resource "aws_rds_cluster_instance" "secondary" {
  count                           = var.existing_global_database_id == null ? 0 : (var.multi_az ? 2 : 1)
  identifier                      = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}-${count.index}"
  cluster_identifier              = aws_rds_cluster.secondary[0].id
  instance_class                  = var.instance_class
  engine                          = aws_rds_cluster.secondary[0].engine
  engine_version                  = aws_rds_cluster.secondary[0].engine_version
  apply_immediately               = true
  auto_minor_version_upgrade      = false
  performance_insights_enabled    = true
  performance_insights_kms_key_id = data.aws_kms_key.main.arn
}
