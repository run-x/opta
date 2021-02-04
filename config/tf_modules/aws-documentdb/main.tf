resource "random_password" "documentdb_auth" {
  length = 20
  special = false
}

data "aws_security_group" "security_group" {
  count = var.security_group == "" ? 1 : 0
  name = "documentdb-sg"
}

resource "aws_docdb_cluster_instance" "cluster_instances" {
  count              = 1
  identifier         = "${var.name}-${count.index}"
  cluster_identifier = aws_docdb_cluster.cluster.id
  instance_class     = var.instance_class
  apply_immediately = true
  auto_minor_version_upgrade = true
}

resource "aws_docdb_cluster" "cluster" {
  cluster_identifier = var.name
  master_username    = "master_user"
  master_password    = random_password.documentdb_auth.result
  db_subnet_group_name = var.subnet_group_name
  engine_version = var.engine_version
  storage_encrypted = true
  kms_key_id = var.kms_account_key_arn
  vpc_security_group_ids = var.security_group == "" ? [data.aws_security_group.security_group[0].id] : [var.security_group]
  apply_immediately = true
}