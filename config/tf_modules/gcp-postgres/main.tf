resource "random_password" "root_auth" {
  length = 20
  special = false
}


# TODO: add encryption key name once out of beta
resource "google_sql_database_instance" "instance" {
  name   = "opta-${var.layer_name}-${var.module_name}"
  database_version = "POSTGRES_${var.engine_version}"

  settings {
    disk_autoresize = true
    disk_type       = "PD_SSD"
    pricing_plan    = "PER_USE"
    availability_type = "REGIONAL"
    tier = var.instance_tier
    ip_configuration {
      ipv4_enabled    = false
      private_network = data.google_compute_network.vpc.id
    }
    backup_configuration {
      binary_log_enabled = true
      enabled            = true
      start_time         = "23:00"
    }
  }

  lifecycle {
    ignore_changes = [settings.disk_size]
  }
}

resource "google_sql_database" "main" {
  instance = google_sql_database_instance.instance.name
  name     = "opta-${var.layer_name}-${var.module_name}"
}

resource "google_sql_user" "root" {
  instance = google_sql_database_instance.instance.name
  name     = "postgres"
  password = random_password.root_auth.result
}