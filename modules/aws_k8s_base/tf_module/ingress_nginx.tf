// NOTE: following this solution for http -> https redirect: https://github.com/kubernetes/ingress-nginx/issues/2724#issuecomment-593769295
resource "helm_release" "ingress-nginx" {
  chart            = "ingress-nginx"
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  version          = contains(["1.19", "1.20", "1.21", "1.22"], var.k8s_version) ? "4.0.17" : "3.40.0"
  namespace        = "ingress-nginx"
  create_namespace = true
  atomic           = true
  cleanup_on_fail  = true
  values = [
    yamlencode({
      controller : {
        podLabels : {
          "opta-ingress-healthcheck" : "yes"
        }
        extraArgs : var.private_key != "" || var.expose_self_signed_ssl ? { default-ssl-certificate : "ingress-nginx/secret-tls" } : {}
        config : local.config
        podAnnotations : {
          "linkerd.io/inject" : "enabled"
          "config.linkerd.io/skip-inbound-ports" : "80,443" // NOTE: should be removed when this is fixed: https://github.com/linkerd/linkerd2/issues/4219
          "cluster-autoscaler.kubernetes.io/safe-to-evict" : "true"
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
        ingressClassResource : {
          default : true
        }

        service : {
          loadBalancerSourceRanges : ["0.0.0.0/0"]
          externalTrafficPolicy : "Local"
          enableHttps : var.cert_arn != "" || var.private_key != "" || var.expose_self_signed_ssl ? true : false
          targetPorts : local.target_ports
          annotations : {
            "service.beta.kubernetes.io/aws-load-balancer-scheme" : "internet-facing"
            "service.beta.kubernetes.io/aws-load-balancer-type" : "external"
            "service.beta.kubernetes.io/aws-load-balancer-nlb-target-type" : "instance"
            "service.beta.kubernetes.io/aws-load-balancer-healthcheck-protocol" : "HTTP"
            "service.beta.kubernetes.io/aws-load-balancer-healthcheck-path" : "/healthz"
            "service.beta.kubernetes.io/aws-load-balancer-backend-protocol" : "ssl"
            "service.beta.kubernetes.io/aws-load-balancer-name" : local.load_balancer_name
            "service.beta.kubernetes.io/aws-load-balancer-access-log-enabled" : true
            "service.beta.kubernetes.io/aws-load-balancer-access-log-s3-bucket-name" : var.s3_log_bucket_name
            "service.beta.kubernetes.io/aws-load-balancer-access-log-s3-bucket-prefix" : "opta-k8s-cluster"
            "service.beta.kubernetes.io/aws-load-balancer-ssl-ports" : local.nginx_tls_ports
            "service.beta.kubernetes.io/aws-load-balancer-ssl-negotiation-policy" : "ELBSecurityPolicy-TLS-1-2-2017-01"
            "service.beta.kubernetes.io/aws-load-balancer-ssl-cert" : var.cert_arn
            "service.beta.kubernetes.io/aws-load-balancer-alpn-policy" : "HTTP2Preferred"
          }
        }
      },
      tcp : var.nginx_extra_tcp_ports,
    }), yamlencode(var.ingress_nginx_values)
  ]
  depends_on = [
    helm_release.linkerd,
    helm_release.opta_base,
    helm_release.load_balancer
  ]
}

data "aws_lb" "ingress-nginx" {
  name       = local.load_balancer_name
  depends_on = [helm_release.ingress-nginx]
}

resource "aws_route53_record" "domain" {
  count = var.domain == "" ? 0 : 1
  name    = var.domain
  type    = "A"
  zone_id = var.zone_id
  allow_overwrite = true
  alias {
    evaluate_target_health = true
    name                   = data.aws_lb.ingress-nginx.dns_name
    zone_id                = data.aws_lb.ingress-nginx.zone_id
  }
}

resource "aws_route53_record" "sub_domain" {
  count = var.domain == "" ? 0 : 1
  name    = "*.${var.domain}"
  type    = "A"
  zone_id = var.zone_id
  allow_overwrite = true
  alias {
    evaluate_target_health = true
    name                   = data.aws_lb.ingress-nginx.dns_name
    zone_id                = data.aws_lb.ingress-nginx.zone_id
  }
}
