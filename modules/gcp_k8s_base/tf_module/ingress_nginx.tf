// NOTE: following this solution for http -> https redirect: https://github.com/kubernetes/ingress-nginx/issues/2724#issuecomment-593769295
resource "helm_release" "ingress-nginx" {
  count            = var.nginx_enabled ? 1 : 0
  chart            = "ingress-nginx"
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
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
          "config.linkerd.io/skip-inbound-ports" : "80,443" // NOTE: should be removed when this is fixed: https://github.com/linkerd/linkerd2/issues/4219
          "linkerd.io/inject" : "enabled"
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
        ingressClassResource : {
          default : true
        }
        containerPort : local.container_ports
        service : {
          loadBalancerSourceRanges : ["0.0.0.0/0"]
          externalTrafficPolicy : "Local"
          enableHttps : true
          targetPorts : local.target_ports
          annotations : {
            "cloud.google.com/neg" : local.annotations
          }
        }
      }
    }), yamlencode(var.ingress_nginx_values)
  ]
  depends_on = [
    helm_release.linkerd,
    helm_release.opta_base
  ]
}