# DATABASE USER  [Configure Database Users](https://docs.atlas.mongodb.com/security-add-mongodb-users/)
resource "random_password" "mongodb_atlas_password" {
  length  = 20
  special = false
}

resource "mongodbatlas_database_user" "user" {
  username           = "opta-${var.layer_name}-${var.module_name}-user"
  password           = random_password.mongodb_atlas_password.result
  project_id         = var.mongodb_atlas_project_id
  auth_database_name = "admin"

  roles {
    role_name     = "readWriteAnyDatabase"
    database_name = "admin"
  }
}