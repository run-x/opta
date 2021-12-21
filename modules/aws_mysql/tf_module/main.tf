data "aws_security_group" "mysql_security_group" {
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

resource "aws_db_instance" "mysql" {
  identifier                      = "opta-${var.layer_name}-${var.module_name}-${random_string.db_name_hash.result}"
  name                            = "app"
  allocated_storage               = var.allocated_storage

  engine                          = "mysql"
  engine_version                  = var.engine_version
  instance_class                  = var.instance_class
  deletion_protection             = var.safety
  backup_retention_period         = 7

  username                        = "mysqldb"
  password                        = random_password.mysql_password.result

  db_subnet_group_name            = "opta-${var.env_name}"
  vpc_security_group_ids          = [data.aws_security_group.mysql_security_group.id]
  kms_key_id                      = data.aws_kms_key.main.arn

  performance_insights_enabled    = true
  performance_insights_kms_key_id = data.aws_kms_key.main.arn

  apply_immediately               = true
  skip_final_snapshot             = true
  storage_encrypted               = true
  auto_minor_version_upgrade      = false

  lifecycle {
    ignore_changes = [storage_encrypted, kms_key_id, identifier]
  }
}