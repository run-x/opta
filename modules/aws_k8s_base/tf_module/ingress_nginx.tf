// NOTE: following this solution for http -> https redirect: https://github.com/kubernetes/ingress-nginx/issues/2724#issuecomment-593769295
resource "helm_release" "ingress-nginx" {
  chart            = "ingress-nginx"
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  version          = "3.27.0"
  namespace        = "ingress-nginx"
  create_namespace = true
  atomic           = true
  cleanup_on_fail  = true
  values = [
    yamlencode({
      controller : {
        extraArgs : var.private_key == "" ? {} : { default-ssl-certificate : "ingress-nginx/secret-tls" }
        config : local.config
        podAnnotations : {
          "linkerd.io/inject" : "enabled"
        }
        resources : {
          requests : {
            cpu : "200m"
            memory : "250Mi"
          }
        }
        autoscaling : {
          enabled : var.nginx_high_availability ? true : false
          minReplicas : var.nginx_high_availability ? 3 : 1
        }
        affinity : {
          podAntiAffinity : {
            preferredDuringSchedulingIgnoredDuringExecution : [
              {
                weight : 50
                podAffinityTerm : {
                  labelSelector : {
                    matchExpressions : [
                      {
                        key : "app.kubernetes.io/name"
                        operator : "In"
                        values : ["ingress-nginx"]
                      },
                      {
                        key : "app.kubernetes.io/instance"
                        operator : "In"
                        values : ["ingress-nginx"]
                      },
                      {
                        key : "app.kubernetes.io/component"
                        operator : "In"
                        values : ["controller"]
                      }
                    ]
                  }
                  topologyKey : "topology.kubernetes.io/zone"
                }
              }
            ]
          }
        }
        containerPort : local.container_ports
        service : {
          loadBalancerSourceRanges : ["0.0.0.0/0"]
          externalTrafficPolicy : "Local"
          enableHttps : var.cert_arn == "" && var.private_key == "" ? false : true
          targetPorts : local.target_ports
          annotations : {
            "service.beta.kubernetes.io/aws-load-balancer-backend-protocol" : "ssl"
            "service.beta.kubernetes.io/aws-load-balancer-name" : "opta-${var.layer_name}-lb"
            "service.beta.kubernetes.io/aws-load-balancer-proxy-protocol" : "*"
            "service.beta.kubernetes.io/aws-load-balancer-type" : "nlb"
            "service.beta.kubernetes.io/aws-load-balancer-access-log-enabled" : true
            "service.beta.kubernetes.io/aws-load-balancer-access-log-s3-bucket-name" : var.s3_log_bucket_name
            "service.beta.kubernetes.io/aws-load-balancer-access-log-s3-bucket-prefix" : "opta-k8s-cluster"
            "service.beta.kubernetes.io/aws-load-balancer-ssl-ports" : local.nginx_tls_ports
            "service.beta.kubernetes.io/aws-load-balancer-ssl-negotiation-policy" : "ELBSecurityPolicy-TLS-1-2-2017-01"
            "service.beta.kubernetes.io/aws-load-balancer-ssl-cert" : var.cert_arn
            "external-dns.alpha.kubernetes.io/hostname" : var.domain == "" ? "" : join(",", [var.domain, "*.${var.domain}"])
          }
        }
      },
      tcp : var.nginx_extra_tcp_ports,
    })
  ]
  depends_on = [
    helm_release.linkerd,
    helm_release.opta_base,
    helm_release.load_balancer
  ]
}
