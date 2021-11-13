output "db_user" {
  value = mongodbatlas_database_user.user.username

}

output "db_password" {

  value     = mongodbatlas_database_user.user.password
  sensitive = true
}

output "mongodb_atlas_connection_string" {
  value = mongodbatlas_cluster.cluster.connection_strings[0].standard_srv
}


