resource "null_resource" "kind-installer" {

  provisioner "local-exec" {
    
    command = <<EOT
      echo "Installing Nginx ingress"
      kubectl --kubeconfig ~/.opta/kind/config apply -f deploy.yaml
    EOT
  }
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
      echo "Removing Nginx ingress"
      kubectl --kubeconfig ~/.opta/kind/config delete -f deploy.yaml
    EOT

    working_dir = path.module
  }
}
