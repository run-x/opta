resource "random_password" "pg_password" {
  length  = 20
  special = false
}

data "aws_security_group" "security_group" {
  name = "opta-${var.env_name}-db-sg"
}

data "aws_kms_key" "main" {
  key_id = "alias/opta-${var.env_name}"
}

resource "random_string" "db_name_hash" {
  length  = 4
  special = false
  upper   = false
}

resource "aws_rds_cluster" "db_cluster" {
  count                   = var.existing_global_database_id == null ? 1 : 0
  cluster_identifier      = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  db_subnet_group_name    = "opta-${var.env_name}"
  database_name           = var.restore_from_snapshot == null ? var.database_name : null
  engine                  = "aurora-postgresql"
  engine_version          = var.engine_version
  master_username         = var.restore_from_snapshot == null ? "postgres" : null
  master_password         = var.restore_from_snapshot == null ? random_password.pg_password.result : null
  vpc_security_group_ids  = concat([data.aws_security_group.security_group.id], var.extra_security_groups_ids)
  backup_retention_period = var.backup_retention_days
  apply_immediately       = true
  skip_final_snapshot     = true
  storage_encrypted       = true
  kms_key_id              = data.aws_kms_key.main.arn
  deletion_protection     = var.safety
  copy_tags_to_snapshot   = true
  snapshot_identifier     = var.restore_from_snapshot
  lifecycle {
    ignore_changes = [storage_encrypted, kms_key_id, cluster_identifier, global_cluster_identifier]
  }
}

resource "aws_rds_cluster_instance" "db_instance" {
  count                           = var.existing_global_database_id == null ? (var.multi_az ? 2 : 1) : 0
  identifier                      = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}-${count.index}"
  cluster_identifier              = aws_rds_cluster.db_cluster[0].id
  instance_class                  = var.instance_class
  engine                          = aws_rds_cluster.db_cluster[0].engine
  engine_version                  = aws_rds_cluster.db_cluster[0].engine_version
  apply_immediately               = true
  auto_minor_version_upgrade      = false
  performance_insights_enabled    = true
  performance_insights_kms_key_id = data.aws_kms_key.main.arn
  lifecycle {
    ignore_changes = [identifier]
  }
}