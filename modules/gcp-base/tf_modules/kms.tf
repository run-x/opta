resource "random_id" "key_suffix" {
  byte_length = 8
}

resource "google_secret_manager_secret" "kms_secret" {
  secret_id = "opta-${var.layer_name}-kms-suffix"

  replication {
    automatic = true
  }
}


resource "google_secret_manager_secret_version" "secret-version-basic" {
  secret = google_secret_manager_secret.kms_secret.id

  secret_data = random_id.key_suffix.hex
}

resource "google_kms_key_ring" "keyring" {
  name     = "opta-${var.layer_name}-${random_id.key_suffix.hex}"
  location = data.google_client_config.current.region
}

resource "google_kms_crypto_key" "key" {
  name            = "opta-${var.layer_name}-${random_id.key_suffix.hex}"
  key_ring        = google_kms_key_ring.keyring.id
  rotation_period = "7776000s"
}

resource "google_kms_crypto_key_iam_member" "gke" {
  crypto_key_id = google_kms_crypto_key.key.id
  member        = "serviceAccount:service-${data.google_project.current.number}@container-engine-robot.iam.gserviceaccount.com"
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
}

resource "google_kms_crypto_key_iam_member" "gcs" {
  crypto_key_id = google_kms_crypto_key.key.id
  role          = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
  member        = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
}