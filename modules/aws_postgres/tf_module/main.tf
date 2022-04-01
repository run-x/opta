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
  database_name           = var.database_name
  engine                  = "aurora-postgresql"
  engine_version          = var.engine_version
  master_username         = "postgres"
  master_password         = random_password.pg_password.result
  vpc_security_group_ids  = [data.aws_security_group.security_group.id]
  backup_retention_period = var.backup_retention_days
  apply_immediately       = true
  skip_final_snapshot     = true
  storage_encrypted       = true
  kms_key_id              = data.aws_kms_key.main.arn
  deletion_protection     = var.safety
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

resource "aws_rds_global_cluster" "global_cluster" {
  count                        = var.create_global_database ? 1 : 0
  force_destroy                = true
  global_cluster_identifier    = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  source_db_cluster_identifier = aws_rds_cluster.db_cluster[0].arn
}

resource "aws_rds_cluster" "secondary" {
  count                     = var.existing_global_database_id == null ? 0 : 1
  cluster_identifier        = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  db_subnet_group_name      = "opta-${var.env_name}"
  global_cluster_identifier = var.existing_global_database_id
  engine                    = "aurora-postgresql"
  engine_version            = var.engine_version
  vpc_security_group_ids    = [data.aws_security_group.security_group.id]
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

resource "time_sleep" "wait_for_db" {
  create_duration = "1s"

  triggers = {
    # This sets up a proper dependency on the RAM association
    primary   = var.existing_global_database_id == null ? aws_rds_cluster_instance.db_instance[0].id : ""
    secondary = var.existing_global_database_id == null ? "" : aws_rds_cluster_instance.secondary[0].id
  }
}