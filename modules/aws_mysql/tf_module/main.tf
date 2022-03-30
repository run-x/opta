data "aws_security_group" "security_group" {
  name = "opta-${var.env_name}-db-sg"
}

data "aws_kms_key" "main" {
  key_id = "alias/opta-${var.env_name}"
}

resource "random_password" "mysql_password" {
  length  = 20
  special = false
}

resource "random_string" "db_name_hash" {
  length  = 4
  special = false
  upper   = false
}

resource "aws_rds_cluster" "db_cluster" {
  cluster_identifier      = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  db_subnet_group_name    = "opta-${var.env_name}"
  database_name           = var.db_name
  engine                  = "aurora-mysql"
  engine_version          = var.engine_version
  master_username         = "mysqldb"
  master_password         = random_password.mysql_password.result
  vpc_security_group_ids  = [data.aws_security_group.security_group.id]
  backup_retention_period = var.backup_retention_days
  apply_immediately       = true
  skip_final_snapshot     = true
  storage_encrypted       = true
  kms_key_id              = data.aws_kms_key.main.arn
  deletion_protection     = var.safety
  lifecycle {
    ignore_changes = [storage_encrypted, kms_key_id, cluster_identifier]
  }
}

resource "aws_rds_cluster_instance" "db_instance" {
  count                      = var.multi_az ? 2 : 1
  identifier                 = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}-${count.index}"
  cluster_identifier         = aws_rds_cluster.db_cluster.id
  instance_class             = var.instance_class
  engine                     = aws_rds_cluster.db_cluster.engine
  engine_version             = aws_rds_cluster.db_cluster.engine_version
  apply_immediately          = true
  auto_minor_version_upgrade = false
  # TODO: Figure out the Performance Insights Configuration.
  #   performance_insights_enabled    = true
  #   performance_insights_kms_key_id = data.aws_kms_key.main.arn
  lifecycle {
    ignore_changes = [identifier]
  }
}