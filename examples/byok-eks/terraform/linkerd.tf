
# install linkerd2 in high availability (HA) mode
module "linkerd2" {
  source  = "run-x/linkerd2/helm"
  version = "0.1.2"
}
