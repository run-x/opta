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
      echo "Installing Nginx ingress"
      kubectl config use-context kind-opta-local-cluster
      kubectl  apply -f deploy.yaml
      echo "Waiting 20s for nginx ingress to stabilize"
      sleep 20 # Wait for nginx to be ready
    EOT
  }
}
