resource "helm_release" "hello-world" {
  chart = "${path.module}/hello-world"
  name = "hello-world"
  values = [
    yamlencode({
      domain: var.hello_world_domain
    })
  ]
  namespace = "default"
  atomic = true
  cleanup_on_fail = true
}