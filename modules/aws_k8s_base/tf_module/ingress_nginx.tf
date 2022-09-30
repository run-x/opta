resource "tls_private_key" "self_signed" {
  count     = var.expose_self_signed_ssl ? 1 : 0
  algorithm = "RSA"
  rsa_bits  = "2048"
}

resource "tls_self_signed_cert" "self_signed" {
  count           = var.expose_self_signed_ssl ? 1 : 0
  private_key_pem = tls_private_key.self_signed[0].private_key_pem
  dns_names       = ["*.elb.${data.aws_region.current.name}.amazonaws.com"]

  subject {
    common_name    = "*.elb.${data.aws_region.current.name}.amazonaws.com"
    organization   = "Opta"
    street_address = []
  }

  validity_period_hours = 87600

  allowed_uses = [
    "key_encipherment",
    "digital_signature",
    "server_auth",
    "client_auth"
  ]
}

resource "aws_acm_certificate" "self_signed" {
  count            = var.expose_self_signed_ssl ? 1 : 0
  private_key      = tls_private_key.self_signed[0].private_key_pem
  certificate_body = tls_self_signed_cert.self_signed[0].cert_pem
}

resource "aws_acm_certificate" "user_provided" {
  count            = var.private_key != "" ? 1 : 0
  private_key      = var.private_key
  certificate_body = join("\n", [var.certificate_body, var.certificate_chain])
}

// NOTE: following this solution for http -> https redirect: https://github.com/kubernetes/ingress-nginx/issues/3724#issuecomment-593769295
resource "helm_release" "ingress-nginx" {
  count            = var.nginx_enabled ? 1 : 0
  chart            = "ingress-nginx"
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  version          = contains(["1.19", "1.20", "1.21", "1.22", "1.23"], var.k8s_version) ? "4.1.4" : "3.40.0"
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
        extraArgs : {}
        config : local.config
        podAnnotations : {
          "linkerd.io/inject" : "enabled"
          "config.linkerd.io/skip-inbound-ports" : "80,443" // NOTE: should be removed when this is fixed: https://github.com/linkerd/linkerd2/issues/4219
          "viz.linkerd.io/tap-enabled" : "true"
          "cluster-autoscaler.kubernetes.io/safe-to-evict" : "true"
          "config.linkerd.io/proxy-cpu-request" : "0.05"
          "config.linkerd.io/proxy-memory-limit" : "20Mi"
          "config.linkerd.io/proxy-memory-request" : "10Mi"
        }
        resources : {
          requests : {
            cpu : "100m"
            memory : "150Mi"
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
            "service.beta.kubernetes.io/aws-load-balancer-ssl-negotiation-policy" : "ELBSecurityPolicy-TLS13-1-2-2021-06"
            "service.beta.kubernetes.io/aws-load-balancer-ssl-cert" : var.expose_self_signed_ssl ? aws_acm_certificate.self_signed[0].arn : (var.private_key != "" ? aws_acm_certificate.user_provided[0].arn : var.cert_arn)
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
  count      = var.nginx_enabled ? 1 : 0
  name       = local.load_balancer_name
  depends_on = [helm_release.ingress-nginx]
}

resource "aws_route53_record" "domain" {
  count           = var.domain == "" || !var.nginx_enabled ? 0 : 1
  name            = var.domain
  type            = "A"
  zone_id         = var.zone_id
  allow_overwrite = true
  alias {
    evaluate_target_health = true
    name                   = data.aws_lb.ingress-nginx[0].dns_name
    zone_id                = data.aws_lb.ingress-nginx[0].zone_id
  }
}

resource "aws_route53_record" "sub_domain" {
  count           = var.domain == "" || var.nginx_enabled ? 0 : 1
  name            = "*.${var.domain}"
  type            = "A"
  zone_id         = var.zone_id
  allow_overwrite = true
  alias {
    evaluate_target_health = true
    name                   = data.aws_lb.ingress-nginx[0].dns_name
    zone_id                = data.aws_lb.ingress-nginx[0].zone_id
  }
}
