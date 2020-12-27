resource "google_sql_database_instance" "main" {
  database_version = "POSTGRES_12"
  name             = var.name

  settings {
    disk_autoresize = true
    disk_size       = 10
    disk_type       = "PD_SSD"
    pricing_plan    = "PER_USE"
    tier            = var.tier
    ip_configuration {
      ipv4_enabled    = false
      private_network = var.gcp_network
    }
    backup_configuration {
      binary_log_enabled = false
      enabled            = false
      start_time         = "23:00"
    }
  }
}

resource "google_sql_database" "main" {
  instance = google_sql_database_instance.main.name
  name     = var.name
}

resource "google_sql_user" "main-user" {
  instance = google_sql_database_instance.main.name
  name     = "postgres"
  password = var.db_password
}
