resource "random_id" "key_suffix" {
  byte_length = 8
}

resource "random_password" "root_auth" {
  length  = 20
  special = false
}

# TODO: currently we are not performing disk encryption as the feature is currently in beta. You may read more about it
# here: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/sql_database_instance#encryption_key_name
# We currently do not wish to tangle with the google-beta provider so we are skipping this feature for now.
resource "google_sql_database_instance" "instance" {
  name                = "opta-${var.layer_name}-${var.module_name}-${random_id.key_suffix.hex}"
  database_version    = "POSTGRES_${var.engine_version}"
  deletion_protection = var.safety

  settings {
    disk_autoresize   = true
    disk_type         = "PD_SSD"
    pricing_plan      = "PER_USE"
    availability_type = "REGIONAL"
    tier              = var.instance_tier
    ip_configuration {
      ipv4_enabled    = false
      private_network = data.google_compute_network.vpc.id
      # Ignore since this requires client certs, VPC is private in anycase
      #tfsec:ignore:google-sql-encrypt-in-transit-data
      require_ssl = false
    }
    backup_configuration {
      enabled    = true
      start_time = "23:00"
    }
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }
    database_flags {
      name  = "log_connections"
      value = "on"
    }
    database_flags {
      name  = "log_disconnections"
      value = "on"
    }
    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }
    database_flags {
      name  = "log_temp_files"
      value = "0"
    }
  }

  lifecycle {
    ignore_changes = [settings[0].disk_size]
  }
}

resource "google_sql_database" "main" {
  instance = google_sql_database_instance.instance.name
  name     = "opta-${var.layer_name}-${var.module_name}-${random_id.key_suffix.hex}"
}

resource "time_sleep" "wait_30_seconds" {
  depends_on = [google_sql_database.main]

  destroy_duration = "30s"
}

resource "google_sql_user" "root" {
  instance = google_sql_database_instance.instance.name
  name     = "postgres"
  password = random_password.root_auth.result

  deletion_policy = "ABANDON"
  depends_on      = [time_sleep.wait_30_seconds]
}
