resource "helm_release" "ingress-nginx" {
  chart = "ingress-nginx"
  name = "ingress-nginx"
  repository = "https://kubernetes.github.io/ingress-nginx"
  namespace = "ingress-nginx"
  create_namespace = true
  atomic = true
  cleanup_on_fail = true
  values = [
    yamlencode({
      controller: {
        config: {
          "use-proxy-protocol": false  # TODO: set this to true and figure out how to play nicely w/ NLB
        }
        podAnnotations: {
          "linkerd.io/inject": "enabled"
        }
        resources: {
          requests: {
            cpu: "200m"
            memory: "250Mi"
          }
        }
        autoscaling: {
          enabled: true
          minReplicas: 3
        }
        affinity: {
          podAntiAffinity: {
            preferredDuringSchedulingIgnoredDuringExecution: [
              {
                weight: 50
                podAffinityTerm: {
                  labelSelector: {
                    matchExpressions: [
                      {
                        key: "app.kubernetes.io/name"
                        operator: "In"
                        values: ["ingress-nginx"]
                      },
                      {
                        key: "app.kubernetes.io/instance"
                        operator: "In"
                        values: ["ingress-nginx"]
                      },
                      {
                        key: "app.kubernetes.io/component"
                        operator: "In"
                        values: ["controller"]
                      }
                    ]
                  }
                  topologyKey: "topology.kubernetes.io/zone"
                }
              }
            ]
          }
        }
        service: {
          loadBalancerSourceRanges: ["0.0.0.0/0"]
          externalTrafficPolicy: "Local"
          enableHttps: var.cert_arn == "" ? false : true
          targetPorts: local.target_ports
          annotations: {
            "service.beta.kubernetes.io/aws-load-balancer-type": "nlb"
            "service.beta.kubernetes.io/aws-load-balancer-ssl-ports": var.cert_arn == "" ? "" : "https"
            "service.beta.kubernetes.io/aws-load-balancer-ssl-cert": var.cert_arn
            "external-dns.alpha.kubernetes.io/hostname": var.domain == "" ? "" : join(",", [var.domain, "*.${var.domain}"])
          }
        }
      }
    })
  ]
}