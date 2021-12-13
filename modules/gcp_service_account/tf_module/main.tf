resource "random_string" "suffix" {
  length  = 4
  upper   = false
  special = false
}

resource "google_service_account" "k8s_service" {
  account_id   = var.explicit_name == null ? "${local.layer_short}-${local.module_short}-${random_string.suffix.result}" : var.explicit_name
  display_name = var.explicit_name == null ? "${local.layer_short}-${local.module_short}-${random_string.suffix.result}" : var.explicit_name
  lifecycle { ignore_changes = [account_id, display_name] }
}

resource "google_service_account_iam_binding" "trust_k8s_workload_idu" {
  count              = length(var.allowed_k8s_services) == 0 ? 0 : 1
  service_account_id = google_service_account.k8s_service.name
  role               = "roles/iam.workloadIdentityUser"
  members            = [for s in var.allowed_k8s_services : "serviceAccount:${data.google_client_config.current.project}.svc.id.goog[${s["namespace"]}/${s["service_account_name"]}]"]

}

resource "google_storage_bucket_iam_member" "bucket_get" {
  for_each = local.get_buckets
  bucket   = each.key
  role     = "roles/storage.legacyBucketReader"
  member   = "serviceAccount:${google_service_account.k8s_service.email}"
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

resource "google_project_iam_member" "project" {
  count   = length(var.additional_iam_roles)
  project = data.google_client_config.current.project
  role    = var.additional_iam_roles[count.index]
  member  = "serviceAccount:${google_service_account.k8s_service.email}"
}
