resource "random_password" "redis_auth" {
  length = 20
  special = false
}

data "aws_security_group" "security_group" {
  count = var.security_group == "" ? 1 : 0
  name = "elasticache-sg"
}

resource "aws_elasticache_replication_group" "redis_cluster" {
  automatic_failover_enabled    = true
  auto_minor_version_upgrade = true
  security_group_ids = var.security_group == "" ? [data.aws_security_group.security_group[0].id] : [var.security_group]
  subnet_group_name = var.subnet_group_name
  replication_group_id          = var.name
  replication_group_description = "Elasticache ${var.name}"
  node_type                     = var.node_type
  engine_version = var.redis_version
  number_cache_clusters         = 2
  port                          = 6379
  apply_immediately = true
  multi_az_enabled = true
  auth_token = random_password.redis_auth.result
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  kms_key_id = var.kms_account_key_arn
  lifecycle {
    ignore_changes = [engine_version]
  }
}