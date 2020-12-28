resource "kubernetes_service" "prod-main-service" {
  metadata {
    labels = {
      "app" = var.name
    }
    name      = var.name
    namespace = var.namespace
  }

  spec {
    selector = {
      "app" = var.name
    }
    type = "NodePort"

    port {
      port        = 80
      protocol    = "TCP"
      target_port = var.target_port
    }
  }
}

resource "kubernetes_ingress" "main-ingress" {
  metadata {
    annotations = (var.public_ip_name == "" ? {} : {
      "kubernetes.io/ingress.global-static-ip-name" = var.public_ip_name
    })
    name      = var.name
    namespace = var.namespace
  }

  spec {
    backend {
      service_name = kubernetes_service.prod-main-service.metadata[0].name
      service_port = kubernetes_service.prod-main-service.spec[0].port[0].port
    }
  }
}

resource "kubernetes_deployment" "main" {
  metadata {
    name = var.name
  }

  spec {
    replicas = var.replicas

    selector {
      match_labels = {
        app = var.name
      }
    }

    template {
      metadata {
        labels = {
          app = var.name
        }
      }

      spec {
        container {
          image = var.image
          name  = "app"

          resources {
            requests {
              cpu    = "50m"
            }
          }
          
          port {
            container_port = var.target_port
          }

          dynamic "env" {
            for_each = var.env_vars

            content {
              name = env.value.name
              value = env.value.value
            }
          }

          readiness_probe {
            http_get {
              path = "/healthcheck"
              port = var.target_port
            }

            initial_delay_seconds = 10
            period_seconds        = 10
          }
        }
      }
    }
  }
}

