resource "null_resource" "local-base" {

  provisioner "local-exec" {
      command = "bash -c config/tf_modules/local-base/install_software.sh"
  }
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
        echo "Uninstalling kind"
        rm -rf ~/.opta/local/kind
        echo "Stopping and removing local docker registry"
        docker stop opta-local-registry
        docker rm opta-local-registry
        echo "Removing ./opta/local directory"
        rm -rf ~/.opta/local
    EOT

    working_dir = path.module
  }
}

resource "null_resource" "k8s-installer" {
  depends_on = [
     "null_resource.local-base"
  ] 
  provisioner "local-exec" {
    command = "bash -c config/tf_modules/local-base/install-cluster.sh"
  }
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
        echo "Removing kind cluster"
        ~/.opta/local/kind  delete cluster --name opta-local-cluster
    EOT

    working_dir = path.module
  }
}


resource "null_resource" "kind-installer" {
  depends_on = [
     "null_resource.k8s-installer"
  ]  
    provisioner "local-exec" {
    
    command = <<EOT
      while [ ! -f ~/.opta/local/kubeconfig ]
      do
        echo "Waiting for cluster to be ready"
        sleep 5 # or less like 0.2
      done
      echo "Installing Nginx ingress"
      kubectl --kubeconfig ~/.opta/local/kubeconfig apply -f config/tf_modules/local-base/deploy.yaml
    EOT
  }
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
      echo "Removing Nginx ingress"
      kubectl --kubeconfig ~/.opta/local/kubeconfig delete -f deploy.yaml
    EOT

    working_dir = path.module
  }
}
