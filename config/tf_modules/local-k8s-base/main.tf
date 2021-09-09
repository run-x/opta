resource "null_resource" "kind-installer" {

  provisioner "local-exec" {
    command = "/bin/bash 'install-cluster.sh'"
  }
  provisioner "local-exec" {
    when    = destroy
    command = <<EOT
        echo "Removing kind cluster"
        ~/.opta/kind/kind  delete cluster --name opta-local-cluster
    EOT

    working_dir = path.module
  }
}
