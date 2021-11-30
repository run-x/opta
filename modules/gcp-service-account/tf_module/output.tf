output "service_account_id" {
  value = google_service_account.k8s_service.account_id
}

output "service_account_email" {
  value = google_service_account.k8s_service.email
}