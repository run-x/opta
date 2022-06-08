
locals {
  load_balancer_name = "${var.cluster_name}-ingress"
}

// deploy the ingress nginx
resource "helm_release" "ingress-nginx" {
  chart            = "ingress-nginx"
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  version          = var.nginx_chart_version
  namespace        = "ingress-nginx"
  create_namespace = true
  atomic           = true
  cleanup_on_fail  = true
  values = [
    yamlencode({
      controller : {
        config : merge({
          ssl-redirect : true
          force-ssl-redirect : true
        }, var.nginx_config)
        podAnnotations : merge({
          "cluster-autoscaler.kubernetes.io/safe-to-evict" : "true",
          "linkerd.io/inject" : "enabled"
        }, var.nginx_extra_pod_annotations)
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
        containerPort : { http : 80, https : 443, healthcheck : 10254 }
        ingressClassResource : {
          default : true
        }

        service : {
          loadBalancerSourceRanges : ["0.0.0.0/0"]
          externalTrafficPolicy : "Local"
          enableHttps : true
          targetPorts : { http : "http", https : "https" }
          annotations : merge({
            // the aws-load-balancer annotations will trigger the creation of the AWS NLB
            # see https://kubernetes-sigs.github.io/aws-load-balancer-controller/v2.2/guide/service/annotations/#lb-type
            "service.beta.kubernetes.io/aws-load-balancer-scheme" : "internet-facing"
            "service.beta.kubernetes.io/aws-load-balancer-type" : "external"
            "service.beta.kubernetes.io/aws-load-balancer-nlb-target-type" : "instance"
            "service.beta.kubernetes.io/aws-load-balancer-healthcheck-protocol" : "HTTP"
            "service.beta.kubernetes.io/aws-load-balancer-healthcheck-path" : "/healthz"
            "service.beta.kubernetes.io/aws-load-balancer-backend-protocol" : "ssl"
            "service.beta.kubernetes.io/aws-load-balancer-name" : local.load_balancer_name
            "service.beta.kubernetes.io/aws-load-balancer-ssl-ports" : "https"
            # https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html#describe-ssl-policies.
            "service.beta.kubernetes.io/aws-load-balancer-ssl-negotiation-policy" : "ELBSecurityPolicy-TLS13-1-2-2021-06"
            "service.beta.kubernetes.io/aws-load-balancer-ssl-cert" : var.load_balancer_cert_arn
            "service.beta.kubernetes.io/aws-load-balancer-alpn-policy" : "HTTP2Preferred"
          }, var.nginx_extra_service_annotations)
        }
      },
    })
  ]
  depends_on = [
    module.linkerd2,
    helm_release.load_balancer,
  ]
}

data "aws_lb" "ingress-nginx" {
  name       = local.load_balancer_name
  depends_on = [helm_release.ingress-nginx]
}

