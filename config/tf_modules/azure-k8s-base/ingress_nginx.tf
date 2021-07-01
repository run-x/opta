data "azurerm_dns_zone" "opta" {
  name = var.hosted_zone_name
}

resource "azurerm_public_ip" "opta" {
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
  network_security_group_name = data.azurerm_network_security_group.opta.name
  resource_group_name         = data.azurerm_resource_group.opta.name
  name                        = "allowhttppublictolb"
  priority                    = 102
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "80"
  destination_address_prefix  = azurerm_public_ip.opta.ip_address
}

resource "azurerm_network_security_rule" "allow_https_to_lb" {
  network_security_group_name = data.azurerm_network_security_group.opta.name
  resource_group_name         = data.azurerm_resource_group.opta.name
  name                        = "allowhttpspublictolb"
  priority                    = 103
  direction                   = "Inbound"
  access                      = "Allow"
  protocol                    = "Tcp"
  source_address_prefix       = "*"
  source_port_range           = "*"
  destination_port_range      = "443"
  destination_address_prefix  = azurerm_public_ip.opta.ip_address
}


resource "random_id" "dns_label" {
  byte_length = 8
}

resource "helm_release" "ingress-nginx" {
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
          loadBalancerIP : azurerm_public_ip.opta.ip_address
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
    })
  ]
  depends_on = [
    helm_release.linkerd
  ]
}