resource "random_password" "pg_password" {
  length = 20
  special = false
}

data "aws_security_group" "security_group" {
  name = "opta-${var.env_name}-db-sg"
}

data "aws_kms_key" "main" {
  key_id = "alias/opta-${var.env_name}"
}

resource "aws_rds_cluster" "db_cluster" {
  cluster_identifier = "opta-${var.layer_name}-${var.module_name}"
  db_subnet_group_name = "opta-${var.env_name}"
  database_name = "app"
  engine = "aurora-postgresql"
  engine_version = var.engine_version
  master_username = "postgres"
  master_password = random_password.pg_password.result
  vpc_security_group_ids = [data.aws_security_group.security_group.id]
  backup_retention_period = 5
  apply_immediately = true
  skip_final_snapshot = true
  storage_encrypted = true
  kms_key_id = data.aws_kms_key.main.arn
  lifecycle {
    ignore_changes = [storage_encrypted, kms_key_id]
  }
}

resource "aws_rds_cluster_instance" "db_instance" {
  count = 1
  identifier         = "opta-${var.layer_name}-${var.module_name}-${count.index}"
  cluster_identifier = aws_rds_cluster.db_cluster.id
  instance_class     = var.instance_class
  engine             = aws_rds_cluster.db_cluster.engine
  engine_version     = aws_rds_cluster.db_cluster.engine_version
  apply_immediately = true
  auto_minor_version_upgrade = false
}