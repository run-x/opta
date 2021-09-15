resource "google_service_account" "k8s_service" {
  account_id   = "${local.env_short}-${local.layer_short}-${local.module_short}"
  display_name = "${local.env_short}-${local.layer_short}-${local.module_short}"
}

resource "google_service_account_iam_binding" "trust_k8s_workload_idu" {
  count              = length(var.allowed_k8s_services) == 0 ? 0 : 1
  service_account_id = google_service_account.k8s_service.name
  role               = "roles/iam.workloadIdentityUser"
  members            = [for s in var.allowed_k8s_services : "serviceAccount:${data.google_client_config.current.project}.svc.id.goog[${s["namespace"]}/${s["service_account_name"]}]"]

}

resource "google_storage_bucket_iam_member" "bucket_viewer" {
  count  = length(var.read_buckets)
  bucket = var.read_buckets[count.index]
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:${google_service_account.k8s_service.email}"
}

resource "google_storage_bucket_iam_member" "viewer" {
  count  = length(var.write_buckets)
  bucket = var.write_buckets[count.index]
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_service_account.k8s_service.email}"
}

