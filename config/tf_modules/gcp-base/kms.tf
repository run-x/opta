resource "google_kms_key_ring" "keyring" {
  name     = "opta-${var.layer_name}"
  location = data.google_client_config.current.region
}

resource "google_kms_crypto_key" "key" {
  name            = "opta-${var.layer_name}"
  key_ring        = google_kms_key_ring.keyring.id
}

resource "google_kms_crypto_key_iam_member" "gke" {
  crypto_key_id = google_kms_crypto_key.key.id
  member = "serviceAccount:service-${data.google_project.current.number}@container-engine-robot.iam.gserviceaccount.com"
  role = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
}