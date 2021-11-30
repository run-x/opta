output "cache_auth_token" {
  value     = aws_elasticache_replication_group.redis_cluster.auth_token
  sensitive = true
}

output "cache_host" {
  value = aws_elasticache_replication_group.redis_cluster.primary_endpoint_address
}
