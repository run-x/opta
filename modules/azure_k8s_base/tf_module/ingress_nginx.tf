resource "azurerm_public_ip" "opta" {
  count               = var.nginx_enabled ? 1 : 0
  name                = "opta-${var.env_name}-k8s-lb-public"
  resource_group_name = data.azurerm_resource_group.opta.name
  location            = data.azurerm_resource_group.opta.location
  allocation_method   = "Static"
  sku                 = "Standard"
  lifecycle {
    ignore_changes = [
      location,
      domain_name_label
    ]
  }
}

data "azurerm_network_security_group" "opta" {
  name                = "opta-${var.env_name}-default"
  resource_group_name = data.azurerm_resource_group.opta.name
}

resource "azurerm_network_security_rule" "allow_http_to_lb" {
  count                       = var.nginx_enabled ? 1 : 0
  network_security_group_name = data.azurerm_network_security_group.opta.name
  resource_group_name         = data.azurerm_resource_group.opta.name
  name                        = "allowhttppublictolb"
  priority                    = 102
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  # ignore since clients from internet connect to LB
  #tfsec:ignore:azure-network-no-public-ingress
  source_address_prefix      = "*"
  source_port_range          = "*"
  destination_port_range     = "80"
  destination_address_prefix = azurerm_public_ip.opta.ip_address
}

resource "azurerm_network_security_rule" "allow_https_to_lb" {
  count                       = var.nginx_enabled ? 1 : 0
  network_security_group_name = data.azurerm_network_security_group.opta.name
  resource_group_name         = data.azurerm_resource_group.opta.name
  name                        = "allowhttpspublictolb"
  priority                    = 103
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  # ignore since clients from internet connect to LB
  #tfsec:ignore:azure-network-no-public-ingress
  source_address_prefix      = "*"
  source_port_range          = "*"
  destination_port_range     = "443"
  destination_address_prefix = azurerm_public_ip.opta.ip_address
}


resource "random_id" "dns_label" {
  byte_length = 8
}

resource "helm_release" "ingress-nginx" {
  count            = var.nginx_enabled ? 1 : 0
  chart            = "ingress-nginx"
  name             = "ingress-nginx"
  repository       = "https://kubernetes.github.io/ingress-nginx"
  namespace        = "ingress-nginx"
  create_namespace = false
  atomic           = true
  cleanup_on_fail  = true
  values = [
    yamlencode({
      controller : {
        extraArgs : var.private_key == "" ? {} : { default-ssl-certificate : "ingress-nginx/secret-tls" }
        config : local.config
        podAnnotations : {
          "config.linkerd.io/skip-inbound-ports" : "80,443" // NOTE: should be removed when this is fixed: https://github.com/linkerd/linkerd2/issues/4219
          "linkerd.io/inject" : "enabled"
          "viz.linkerd.io/tap-enabled" : "true"
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
          loadBalancerIP : azurerm_public_ip.opta[0].ip_address
          loadBalancerSourceRanges : ["0.0.0.0/0"]
          externalTrafficPolicy : "Local"
          enableHttps : true
          targetPorts : local.target_ports
          annotations : {
            "service.beta.kubernetes.io/azure-load-balancer-resource-group" : data.azurerm_resource_group.opta.name
            "service.beta.kubernetes.io/azure-dns-label-name" : "opta-${var.env_name}-${random_id.dns_label.hex}"
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