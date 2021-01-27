output "value" {
  value = kubernetes_secret.secret.data.value
}
