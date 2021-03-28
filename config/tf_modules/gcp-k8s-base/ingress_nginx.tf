// NOTE: following this solution for http -> https redirect: https://github.com/kubernetes/ingress-nginx/issues/2724#issuecomment-593769295
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
        config: local.config
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
          enabled: var.high_availability ? true : false
          minReplicas: var.high_availability ? 3 : 1
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
        containerPort: local.container_ports
        service: {
          loadBalancerSourceRanges: ["0.0.0.0/0"]
          externalTrafficPolicy: "Local"
          enableHttps: false
          targetPorts: local.target_ports
          annotations: {
            "cloud.google.com/neg": local.annotations
          }
        }
      }
    })
  ]
}