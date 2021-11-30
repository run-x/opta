output "cache_auth_token" {
  value     = google_redis_instance.main.auth_string
  sensitive = true
}

output "cache_host" {
  value = google_redis_instance.main.host
}
