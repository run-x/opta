resource "kubernetes_secret" "secret" {
  metadata {
    name = var.name
  }

  lifecycle {
    ignore_changes = [ data ]
  }

  data = {
    value = ""
  }
}
