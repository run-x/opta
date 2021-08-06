resource "google_storage_bucket" "bucket" {
  name     = var.bucket_name
  location = data.google_client_config.current.region
  encryption {
    default_kms_key_name = data.google_kms_crypto_key.kms.id
  }
  force_destroy               = true
  uniform_bucket_level_access = true
}

resource "google_storage_bucket_iam_member" "viewer" {
  count  = var.block_public ? 0 : 1
  bucket = google_storage_bucket.bucket.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}