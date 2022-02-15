resource "null_resource" "local-base" {

  provisioner "local-exec" {
    working_dir = path.module
    command     = "bash ./install_software.sh"
  }
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
        echo "Uninstalling kind"
        rm -rf $HOME/.opta/local/kind
        echo "Stopping and removing local docker registry"
        docker stop opta-local-registry
        docker rm opta-local-registry
        echo "Removing ./opta/local directory"
        rm -rf $HOME/.opta/local
    EOT

    working_dir = path.module
  }
}

resource "null_resource" "k8s-installer" {
  depends_on = [
    null_resource.local-base
  ]
  provisioner "local-exec" {
    working_dir = path.module
    command     = "bash -c ./install-cluster.sh"
  }
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
        echo "Removing kind cluster"
        $HOME/.opta/local/kind  delete cluster --name opta-local-cluster
    EOT

    working_dir = path.module
  }
}


resource "null_resource" "kind-installer" {
  depends_on = [
    null_resource.k8s-installer
  ]
  provisioner "local-exec" {
    working_dir = path.module
    command     = <<EOT
      kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
      kubectl wait --namespace ingress-nginx --for=condition=ready pod --selector=app.kubernetes.io/component=controller --timeout=90s
    EOT
  }
}
