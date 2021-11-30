resource "random_password" "redis_auth" {
  length  = 20
  special = false
}

resource "random_string" "redis_name_hash" {
  length  = 4
  special = false
  upper   = false
}

data "aws_security_group" "security_group" {
  name = "opta-${var.env_name}-elasticache-sg"
}

data "aws_kms_key" "main" {
  key_id = "alias/opta-${var.env_name}"
}

resource "aws_elasticache_replication_group" "redis_cluster" {
  automatic_failover_enabled    = true
  auto_minor_version_upgrade    = true
  security_group_ids            = [data.aws_security_group.security_group.id]
  subnet_group_name             = "opta-${var.env_name}"
  replication_group_id          = "opta-${var.layer_name}-${var.module_name}-${random_string.redis_name_hash.result}"
  replication_group_description = "Elasticache opta-${var.layer_name}-${var.module_name}-${random_string.redis_name_hash.result}"
  node_type                     = var.node_type
  engine_version                = var.redis_version
  number_cache_clusters         = 2
  port                          = 6379
  apply_immediately             = true
  multi_az_enabled              = true
  auth_token                    = random_password.redis_auth.result
  transit_encryption_enabled    = true
  at_rest_encryption_enabled    = true
  kms_key_id                    = data.aws_kms_key.main.arn
  snapshot_window               = var.snapshot_window
  snapshot_retention_limit      = var.snapshot_retention_limit
  lifecycle {
    ignore_changes = [engine_version, replication_group_id, replication_group_description]
  }
}