terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 3.51.0"
    }
  }
}

// TODO: These need to be enabled in a separate step
resource "google_project_service" "service-networking" {
  service = "servicenetworking.googleapis.com"
}

resource "google_project_service" "compute" {
  service = "compute.googleapis.com"
}

resource "google_project_service" "container" {
  service = "container.googleapis.com"
}

resource "google_storage_bucket" "tf_state" {
  name = "opta_tf_state_${var.name}"
}
